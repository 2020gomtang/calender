import json
import jwt  # 🚀 JWT 토큰 수동 해독을 위해 소환!
from django.conf import settings
from django.http import JsonResponse
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.db import models

from Plan.models import Plan, PlanHistory
from User.models import Friend, User
from Post.models import PostComment


# 🚀 모든 POST/DELETE 요청에 대해 CSRF 면제권을 주어 통신 바리케이트를 해제합니다.
@method_decorator(csrf_exempt, name='dispatch')
class PostBoardView(TemplateView):
    template_name = 'Post/board_main.html'

    # 📡 [핵심 무기] 헤더에서 JWT 토큰을 수동으로 찢어서 진짜 로그인한 유저를 찾아내는 해독 엔진
    def get_authenticated_user(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            # 유저님이 로그인할 때 발행한 settings.SECRET_KEY로 정밀 복호화
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            username = payload.get('username') or payload.get('user_id')
            if username:
                return User.objects.filter(username=username).first()
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
        return None

    def get(self, request, *args, **kwargs):
        # 1. 브라우저 주소창 다이렉트 진입 시 HTML 화면 프리패스 서빙
        if 'application/json' not in request.headers.get('Accept', ''):
            return render(request, self.template_name)

        # 2. 🚀 [진짜 토큰 인터셉트] 유령 유저(AnonymousUser) 문제를 원천 차단합니다.
        db_user = self.get_authenticated_user(request)

        # 토큰이 유효하지 않거나 비로그인 상태라면 에러를 안 뿜고 얌전하게 빈 피드 반환 (프론트 발작 방지)
        if not db_user:
            print("💡 [PostBoardView] 유효한 토큰 없음 -> 빈 피드 데이터 서빙 (200)")
            return JsonResponse({"feed": []}, status=200)

        try:
            u_name = db_user.username  # 토큰 주인의 진짜 아이디 장착

            # 내 친구들의 username 리스트 확보 (_id 계열 매핑 추적)
            friend_usernames = Friend.objects.filter(
                from_user_id=u_name
            ).values_list('to_user_id', flat=True)

            # 🚀 [완벽 교정 쿼리] 내 글이든 친구 글이든 무조건 'is_shared=True'(공유 상태)인 알맹이만 피드판에 긁어옵니다!
            active_plans = Plan.objects.filter(
                models.Q(user__username=u_name, is_shared=True) | models.Q(user__username__in=friend_usernames,
                                                                           is_shared=True)
            ).select_related('user').prefetch_related('post_comments__user').order_by('-created_at')

            past_histories = PlanHistory.objects.filter(
                models.Q(user__username=u_name, is_shared=True) | models.Q(user__username__in=friend_usernames,
                                                                           is_shared=True)
            ).select_related('user').prefetch_related('post_comments__user').order_by('-completed_at')

            feed_items = []

            for p in active_plans:
                feed_items.append({
                    "id": p.id,
                    "type": "ACTIVE",
                    "user": p.user.username,
                    "is_me": p.user.username == u_name,  # 🚀 내가 쓴 글이면 프론트에서 토글 버튼을 쥐어줍니다.
                    "category": p.category,
                    "title": p.title,
                    "content": p.content,
                    "ai_duration_hours": p.ai_duration_hours,
                    "status": p.status,
                    "is_shared": p.is_shared,
                    "date": p.assigned_date.strftime('%Y-%m-%d') if p.assigned_date else "미지정",
                    "comments": [{
                        "comment_id": c.id,
                        "username": c.user.username,
                        "content": c.content,
                        "is_comment_owner": c.user.username == u_name,
                        "created_at": c.created_at.strftime('%m-%d %H:%M')
                    } for c in p.post_comments.all()]
                })

            for h in past_histories:
                feed_items.append({
                    "id": h.id,
                    "type": "HISTORY",
                    "user": h.user.username,
                    "is_me": h.user.username == u_name,
                    "category": h.category,
                    "title": h.title,
                    "content": "성공적으로 완수되어 보관된 기록입니다.",
                    "ai_duration_hours": None,
                    "status": h.result,
                    "is_shared": h.is_shared,
                    "date": h.completed_at.strftime('%Y-%m-%d'),
                    "comments": [{
                        "comment_id": c.id,
                        "username": c.user.username,
                        "content": c.content,
                        "is_comment_owner": c.user.username == u_name,
                        "created_at": c.created_at.strftime('%m-%d %H:%M')
                    } for c in h.post_comments.all()]
                })

            return JsonResponse({"feed": feed_items}, status=200)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"message": f"피드 연동 실패: {str(e)}"}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PostCommentCreateView(View):
    def post(self, request, *args, **kwargs):
        try:
            # 1. 토큰에서 username 파싱
            auth_header = request.headers.get('Authorization', '')
            u_name = None
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                u_name = payload.get('username') or payload.get('user_id')

            if not u_name:
                return JsonResponse({"message": "로그인이 필요합니다."}, status=401)

            # 🚀 [이 줄이 핵심!] 장고가 그토록 원하는 진짜 'User 인스턴스' 객체를 먼저 조회합니다.
            try:
                db_user = User.objects.get(username=u_name)
            except User.DoesNotExist:
                return JsonResponse({"message": "존재하지 않는 유저입니다."}, status=404)

            data = json.loads(request.body)
            target_id = data.get('target_id')
            target_type = data.get('target_type')
            content = data.get('content')

            # 🚀 2. 인서트할 때 문자열(u_name) 대신 방금 찾은 진짜 객체(db_user)를 넘겨줍니다!
            if target_type == "ACTIVE":
                try:
                    target_plan = Plan.objects.get(id=target_id)
                except Plan.DoesNotExist:
                    return JsonResponse({"message": "존재하지 않는 계획입니다."}, status=404)

                # 🎯 여기를 u_name이 아니라 db_user로 꽂아줍니다!
                PostComment.objects.create(user=db_user, plan=target_plan, content=content)

            elif target_type == "HISTORY":
                try:
                    target_history = PlanHistory.objects.get(id=target_id)
                except PlanHistory.DoesNotExist:
                    return JsonResponse({"message": "존재하지 않는 완료 기록입니다."}, status=404)

                # 🎯 여기를 u_name이 아니라 db_user로 꽂아줍니다!
                PostComment.objects.create(user=db_user, plan_history=target_history, content=content)

            return JsonResponse({"message": "댓글이 정상적으로 등록되었습니다."}, status=201)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"message": f"서버 오류: {str(e)}"}, status=500)
@method_decorator(csrf_exempt, name='dispatch')
class DeleteCommentView(View):
    def delete(self, request, comment_id, *args, **kwargs):
        try:
            # 안전장치 토큰 파싱
            auth_header = request.headers.get('Authorization', '')
            u_name = None
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                u_name = payload.get('username') or payload.get('user_id')

            if not u_name:
                return JsonResponse({"message": "인증 정보가 없습니다."}, status=401)

            comment = PostComment.objects.get(id=comment_id)
            if comment.user.username != u_name:
                return JsonResponse({"message": "본인이 작성한 댓글만 삭제할 수 있습니다."}, status=403)

            comment.delete()
            return JsonResponse({"message": "댓글이 삭제되었습니다."}, status=200)
        except PostComment.DoesNotExist:
            return JsonResponse({"message": "존재하지 않는 댓글입니다."}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class ToggleShareView(View):
    def post(self, request, *args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization', '')
            u_name = None
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                u_name = payload.get('username') or payload.get('user_id')

            if not u_name:
                return JsonResponse({"message": "인증 정보가 없습니다."}, status=401)

            data = json.loads(request.body)
            target_id = data.get('target_id')
            target_type = data.get('target_type')

            if target_type == "ACTIVE":
                item = Plan.objects.get(id=target_id, user__username=u_name)
            else:
                item = PlanHistory.objects.get(id=target_id, user__username=u_name)

            item.is_shared = not item.is_shared
            item.save()

            status_str = "공유 중" if item.is_shared else "비공개(공유취소)"
            return JsonResponse({"message": f"해당 계획이 {status_str} 상태로 변경되었습니다.", "is_shared": item.is_shared},
                                status=200)
        except Exception as e:
            return JsonResponse({"message": "권한이 없거나 찾을 수 없는 글입니다."}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class PostShareToggleView(View):
    def post(self, request, *args, **kwargs):
        try:
            # 🚀 안전하게 헤더에서 직접 파싱 처리하여 토큰 소유주 확보
            auth_header = request.headers.get('Authorization', '')
            u_name = None
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                u_name = payload.get('username') or payload.get('user_id')

            if not u_name:
                return JsonResponse({"message": "인증 정보가 없습니다."}, status=401)

            data = json.loads(request.body)
            target_id = data.get('target_id')
            target_type = data.get('target_type')

            if target_type == "ACTIVE":
                plan = Plan.objects.get(id=target_id, user__username=u_name)
                plan.is_shared = not getattr(plan, 'is_shared', False)
                plan.save()
                msg = "🔓 계획이 공유 게시판에 공개되었습니다." if plan.is_shared else "🔒 계획이 나만보기로 전환되었습니다."
                return JsonResponse({"message": msg, "is_shared": plan.is_shared}, status=200)

            elif target_type == "HISTORY":
                history = PlanHistory.objects.get(id=target_id, user__username=u_name)
                history.is_shared = not getattr(history, 'is_shared', False)
                history.save()
                msg = "🔓 성공 기록이 공유되었습니다." if history.is_shared else "🔒 성공 기록이 숨겨졌습니다."
                return JsonResponse({"message": msg, "is_shared": history.is_shared}, status=200)

            return JsonResponse({"message": "올바르지 않은 타겟 타입입니다."}, status=400)

        except (Plan.DoesNotExist, PlanHistory.DoesNotExist):
            return JsonResponse({"message": "해당 계획을 찾을 수 없거나 소유권이 없습니다."}, status=404)
        except Exception as e:
            return JsonResponse({"message": f"토글 처리 중 서버 오류: {str(e)}"}, status=500)