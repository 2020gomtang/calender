import json
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Friend
from User.decorators import login_required_jwt

User = get_user_model()


@method_decorator(login_required_jwt, name='dispatch')
class FriendView(TemplateView):
    # 💡 1. 친구 관리 메인 템플릿 화면 열기
    template_name = 'Friend/friend_main.html'

    # 💡 2. 현재 내 친구 목록 불러오기 (GET)
    def get(self, request, *args, **kwargs):
        # 주소창을 통해 브라우저 화면 자체를 요청한 거라면 HTML 서빙
        if 'application/json' not in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)

        # 자바스크립트가 데이터를 요청(API 호출)한 거라면 JSON 반환
        # 내가 등록한 친구와 나를 등록한 친구를 모두 합쳐서 "서로 친구"인 목록 도출
        friendships = Friend.objects.filter(from_user=request.user)

        friend_list = []
        for f in friendships:
            friend_list.append({
                "friendship_id": f.id,
                "id": f.to_user.id,
                "username": f.to_user.username,
                "email": f.to_user.email
            })

        return JsonResponse({"friends": friend_list}, status=200)

    # 💡 3. 아이디 또는 이메일로 친구 찾아서 추가하기 (POST)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            search_query = data.get('search_query')  # 유저가 입력한 ID 혹은 이메일 텍스트

            if not search_query:
                return JsonResponse({"message": "찾으실 아이디 또는 이메일을 입력해주세요."}, status=400)

            # 자기 자신을 추가하려는 꼼수 차단
            if search_query == request.user.username or search_query == request.user.email:
                return JsonResponse({"message": "본인 자신은 친구로 추가할 수 없습니다."}, status=400)

            try:
                # 아이디 혹은 이메일이 정확히 일치하는 타겟 유저 검색
                target_user = User.objects.get(Q(username=search_query) | Q(email=search_query))
            except User.DoesNotExist:
                return JsonResponse({"message": "존재하지 않는 유저입니다. 다시 확인해주세요."}, status=404)

            # 이미 친구인지 아닌지 상호 검사
            if Friend.objects.filter(from_user=request.user, to_user=target_user).exists():
                return JsonResponse({"message": "이미 친구로 등록된 유저입니다."}, status=400)

            # 친구 관계 생성
            Friend.objects.create(from_user=request.user, to_user=target_user)

            return JsonResponse({
                "message": f"[{target_user.username}] 님과 성공적으로 친구가 되었습니다!"
            }, status=201)

        except Exception as e:
            return JsonResponse({"message": f"서버 오류: {str(e)}"}, status=500)

    # 💡 4. 친구 삭제하기 (DELETE)
    def delete(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            target_friend_id = data.get('friend_user_id')  # 삭제할 상대방 유저의 고유 PK ID

            # 내 친구 목록 중 해당 유저와의 관계 링크 탐색
            friendship = Friend.objects.filter(from_user=request.user, to_user_id=target_friend_id)

            if not friendship.exists():
                return JsonResponse({"message": "친구 관계가 존재하지 않거나 이미 삭제되었습니다."}, status=404)

            friendship.delete()
            return JsonResponse({"message": "친구 관계가 정상적으로 끊어졌습니다."}, status=200)

        except Exception as e:
            return JsonResponse({"message": f"서버 오류: {str(e)}"}, status=500)