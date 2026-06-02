import json
import jwt  # 🚀 JWT 토큰 직접 해독을 위해 소환!
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# 통합된 모델과 유틸리티 함수 가져오기
from .models import User, Friend
from .utils import generate_access_token


class MainWorkspaceView(TemplateView):
    template_name = 'User/main.html'


# ➊ 회원가입 View
@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(TemplateView):
    template_name = 'User/signup.html'

    def post(self, request):
        try:
            data = json.loads(request.body)

            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            name = data.get('name')

            if not (username and password and email and name):
                return JsonResponse({"message": "필수 입력 값이 누락되었습니다."}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"message": "이미 존재하는 아이디입니다."}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({"message": "이미 등록된 이메일입니다."}, status=400)

            hashed_password = make_password(password)
            user = User.objects.create(
                username=username,
                password=hashed_password,
                email=email,
                name=name
            )

            return JsonResponse({
                "message": "회원가입이 완료되었습니다.",
                "user": {"id": user.id, "username": user.username, "name": user.name}
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"message": "잘못된 JSON 형식입니다."}, status=400)


# ➋ 로그인 View
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(TemplateView):
    template_name = 'User/login.html'

    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not (username and password):
                return JsonResponse({"message": "아이디와 비밀번호를 모두 입력해주세요."}, status=400)

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({"message": "아이디 또는 비밀번호가 일치하지 않습니다."}, status=401)

            if not check_password(password, user.password):
                return JsonResponse({"message": "아이디 또는 비밀번호가 일치하지 않습니다."}, status=401)

            # 로그인 성공 시 JWT 토큰 발행
            token = generate_access_token(user)

            return JsonResponse({
                "message": "로그인에 성공했습니다.",
                "access_token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"message": "잘못된 JSON 형식입니다."}, status=400)


# 🚀 [대통합 마감] 친구 기능 올인원 제어 View
@method_decorator(csrf_exempt, name='dispatch')
class UserFriendView(View):

    # 📡 [핵심 무기] 프론트엔드가 실어 보낸 Bearer 토큰을 가져와 직접 해독하는 스크립트 엔진
    def get_authenticated_username(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        # 'Bearer <토큰>' 형태에서 토큰 알맹이만 분리
        token = auth_header.split(' ')[1]
        try:
            # generate_access_token 만들 때 사용한 settings.SECRET_KEY로 정밀 복호화
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            # 발급 구조에 따라 'username' 또는 'user_id' 중 들어있는 값 매핑
            return payload.get('username') or payload.get('user_id')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    # 💡 1. 내 친구 목록 가져오기 (GET)
    def get(self, request, *args, **kwargs):
        if 'application/json' not in request.headers.get('Accept', ''):
            return render(request, 'Friend/friend_main.html')

        try:
            # 🚀 토큰 검증해서 내 진짜 username 알아내기
            my_username = self.get_authenticated_username(request)
            if not my_username:
                return JsonResponse({"message": "인증 토큰이 없거나 만료되었습니다. 다시 로그인해 주세요."}, status=401)

            # 내 아이디가 '보낸 사람'으로 등록된 관계 싹 긁어오기
            friendships = Friend.objects.filter(from_user_id=my_username)
            friend_list = []
            for f in friendships:
                friend_list.append({
                    "friendship_id": f.id,
                    "username": f.to_user_id,  # 상대방 문자열 ID 매칭
                    "email": f.to_user.email if hasattr(f.to_user, 'email') else ""
                })
            return JsonResponse({"friends": friend_list}, status=200)
        except Exception as e:
            return JsonResponse({"friends": [], "error": str(e)}, status=500)

    # 💡 2. 진짜 내 토큰 기반으로 친구 추가 (POST)
    def post(self, request, *args, **kwargs):
        try:
            # 🚀 [토큰 긴급 수수] 게스트 계정 다 치우고 진짜 내 아이디 파싱 성공!
            my_username = self.get_authenticated_username(request)
            if not my_username:
                return JsonResponse({"message": "인증 정보가 유효하지 않습니다. 다시 로그인해 주세요."}, status=401)

            data = json.loads(request.body)
            search_query = data.get('search_query')  # 유저님이 입력창에 입력한 상대방 ID/이메일

            if not search_query:
                return JsonResponse({"message": "찾으실 아이디 또는 이메일을 입력해주세요."}, status=400)

            if search_query == my_username:
                return JsonResponse({"message": "본인 자신은 친구로 추가할 수 없습니다."}, status=400)

            # 🔍 [유저 DB 스캔] 추가하려는 대상이 실제 우리 유저 테이블에 실재하는지 검증
            try:
                target_user = User.objects.get(Q(username=search_query) | Q(email=search_query))
            except User.DoesNotExist:
                return JsonResponse({"message": "존재하지 않는 유저입니다. 다시 확인해주세요."}, status=404)

            # 중복 검사 (이미 맺어진 선이 있는지 체크)
            if Friend.objects.filter(from_user_id=my_username, to_user_id=target_user.username).exists():
                return JsonResponse({"message": "이미 친구로 등록된 유저입니다."}, status=400)

            # 🤝 [디비 인서트] 토큰에서 추출한 '나'의 ID와 찾은 '상대방'의 ID를 정확하게 릴레이션 결합
            Friend.objects.create(
                from_user_id=my_username,
                to_user_id=target_user.username
            )

            return JsonResponse({
                "message": f"[{target_user.username}] 님을 성공적으로 친구 추가했습니다!"
            }, status=201)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"message": f"서버 오류: {str(e)}"}, status=500)

    # 💡 3. 친구 해제 (DELETE)
    def delete(self, request, *args, **kwargs):
        try:
            # 🚀 삭제할 때도 토큰 소유주 본인 확인 거치기
            my_username = self.get_authenticated_username(request)
            if not my_username:
                return JsonResponse({"message": "인증 토큰이 유효하지 않습니다."}, status=401)

            data = json.loads(request.body)
            target_friend_username = data.get('friend_username')

            friendship = Friend.objects.filter(
                from_user_id=my_username,
                to_user_id=target_friend_username
            )

            if not friendship.exists():
                return JsonResponse({"message": "친구 관계가 존재하지 않거나 이미 삭제되었습니다."}, status=404)

            friendship.delete()
            return JsonResponse({"message": "친구 관계가 정상적으로 끊어졌습니다."}, status=200)

        except Exception as e:
            return JsonResponse({"message": f"서버 오류: {str(e)}"}, status=500)