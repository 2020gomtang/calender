import json
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.hashers import make_password, check_password
from .models import User
from .utils import generate_access_token
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


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

            # 필수 값 검증
            if not (username and password and email and name):
                return JsonResponse({"message": "필수 입력 값이 누락되었습니다."}, status=400)

            # 아이디 및 이메일 중복 체크
            if User.objects.filter(username=username).exists():
                return JsonResponse({"message": "이미 존재하는 아이디입니다."}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({"message": "이미 등록된 이메일입니다."}, status=400)

            # 비밀번호 해시 암호화 후 유저 생성
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

            # 💡 로그인 성공 시 JWT 토큰 발행
            token = generate_access_token(user)

            return JsonResponse({
                "message": "로그인에 성공했습니다.",
                "access_token": token,  # 💡 클라이언트는 이 토큰을 저장해두고 요청 때마다 사용합니다.
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"message": "잘못된 JSON 형식입니다."}, status=400)
# User/views.py 맨 아래에 추가


