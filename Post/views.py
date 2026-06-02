# Post/views.py
import json
import datetime
from django.http import JsonResponse
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.db import models  # 💡 필수 추가: models.Q 장동을 위해 반드시 필요합니다!

from Plan.models import Plan, PlanHistory
from Friend.models import Friend
from Post.models import PostComment
from User.decorators import login_required_jwt


@method_decorator(login_required_jwt, name='dispatch')
class PostBoardView(TemplateView):
    template_name = 'Post/board_main.html'

    def get(self, request, *args, **kwargs):
        if 'application/json' not in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)

        friend_ids = Friend.objects.filter(from_user=request.user).values_list('to_user_id', flat=True)

        # 💡 models.Q 객체를 사용하여 나+친구 공유글 필터링
        active_plans = Plan.objects.filter(
            models.Q(user=request.user) | models.Q(user_id__in=friend_ids, is_shared=True)
        ).select_related('user').prefetch_related('post_comments__user').order_by('-created_at')

        past_histories = PlanHistory.objects.filter(
            models.Q(user=request.user) | models.Q(user_id__in=friend_ids, is_shared=True)
        ).select_related('user').prefetch_related('post_comments__user').order_by('-completed_at')

        feed_items = []

        # 💡 껍데기였던 피드 데이터 패킹 로직을 데이터 규격에 맞게 완벽히 마감합니다.
        for p in active_plans:
            feed_items.append({
                "id": p.id,
                "type": "ACTIVE",
                "user": p.user.username,
                "is_me": p.user == request.user,
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
                    "is_comment_owner": c.user == request.user,
                    "created_at": c.created_at.strftime('%m-%d %H:%M')
                } for c in p.post_comments.all()]
            })

        for h in past_histories:
            feed_items.append({
                "id": h.id,
                "type": "HISTORY",
                "user": h.user.username,
                "is_me": h.user == request.user,
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
                    "is_comment_owner": c.user == request.user,
                    "created_at": c.created_at.strftime('%m-%d %H:%M')
                } for c in h.post_comments.all()]
            })

        return JsonResponse({"feed": feed_items}, status=200)


# 💡 빽나던 문제의 근본적 해결책: 누락되었던 댓글 생성 전용 클래스 뷰 수식 확보
@method_decorator(login_required_jwt, name='dispatch')
class PostCommentCreateView(View):
    """
    게시판 피드 카드에서 호출하는 실시간 댓글 등록 API
    """

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            target_id = data.get('target_id')
            target_type = data.get('target_type')  # "ACTIVE" 또는 "HISTORY"
            content = data.get('content')

            if not content:
                return JsonResponse({"message": "댓글 내용을 입력해주세요."}, status=400)

            if target_type == "ACTIVE":
                PostComment.objects.create(user=request.user, plan_id=target_id, content=content)
            elif target_type == "HISTORY":
                PostComment.objects.create(user=request.user, plan_history_id=target_id, content=content)
            else:
                return JsonResponse({"message": "올바르지 않은 타겟 타입입니다."}, status=400)

            return JsonResponse({"message": "댓글이 정상적으로 등록되었습니다."}, status=201)
        except Exception as e:
            return JsonResponse({"message": f"서버 오류: {str(e)}"}, status=500)


@method_decorator(login_required_jwt, name='dispatch')
class DeleteCommentView(View):
    """
    ❌ 댓글 삭제 API
    """

    def delete(self, request, comment_id, *args, **kwargs):
        try:
            comment = PostComment.objects.get(id=comment_id)
            if comment.user != request.user:
                return JsonResponse({"message": "본인이 작성한 댓글만 삭제할 수 있습니다."}, status=403)

            comment.delete()
            return JsonResponse({"message": "댓글이 삭제되었습니다."}, status=200)
        except PostComment.DoesNotExist:
            return JsonResponse({"message": "존재하지 않는 댓글입니다."}, status=404)


@method_decorator(login_required_jwt, name='dispatch')
class ToggleShareView(View):
    """
    🔒 공유 취소 / 다시 공유 토글 API
    """

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            target_id = data.get('target_id')
            target_type = data.get('target_type')

            if target_type == "ACTIVE":
                item = Plan.objects.get(id=target_id, user=request.user)
            else:
                item = PlanHistory.objects.get(id=target_id, user=request.user)

            item.is_shared = not item.is_shared
            item.save()

            status_str = "공유 중" if item.is_shared else "비공개(공유취소)"
            return JsonResponse({"message": f"해당 계획이 {status_str} 상태로 변경되었습니다.", "is_shared": item.is_shared},
                                status=200)
        except Exception as e:
            return JsonResponse({"message": "권한이 없거나 찾을 수 없는 글입니다."}, status=404)