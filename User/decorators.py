from django.http import JsonResponse
from .utils import validate_token
from .models import User


def login_required_jwt(func):
    def wrapper(request, *args, **kwargs):
        # HTTP Header에서 Authorization 값을 가져옴
        auth_header = request.headers.get('Authorization', None)

        if not auth_header:
            return JsonResponse({"message": "토큰이 제공되지 않았습니다."}, status=401)

        try:
            # 보통 헤더에 "Bearer <토큰>" 형태로 들어오므로 분리 처리
            prefix, token = auth_header.split(' ')
            if prefix != 'Bearer':
                return JsonResponse({"message": "토큰 형식이 올바르지 않습니다. 'Bearer <토큰>' 형태여야 합니다."}, status=401)

            # 토큰 복호화 및 검증
            payload = validate_token(token)
            if not payload:
                return JsonResponse({"message": "토큰이 만료되었거나 유효하지 않습니다."}, status=401)

            # 토큰 속 user_id로 실제 존재하는 유저인지 확인 후 request에 심어줌
            request.user = User.objects.get(id=payload['user_id'])

        except (ValueError, User.DoesNotExist):
            return JsonResponse({"message": "유효하지 않은 토큰이거나 존재하지 않는 유저입니다."}, status=401)

        return func(request, *args, **kwargs)

    return wrapper