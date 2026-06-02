from django.http import JsonResponse
from .utils import validate_token
from .models import User

def login_required_jwt(func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', None)

        if not auth_header:
            return JsonResponse({"message": "토큰이 제공되지 않았습니다."}, status=401)

        try:
            prefix, token = auth_header.split(' ')
            if prefix != 'Bearer':
                return JsonResponse({"message": "토큰 형식이 올바르지 않습니다."}, status=401)

            payload = validate_token(token)
            if not payload:
                return JsonResponse({"message": "토큰이 만료되었거나 유효하지 않습니다."}, status=401)

            # 🚀 [교정] 무조건 문자열 아이디('username')를 최우선으로 쥐어짜 냅니다.
            username_val = payload.get('username')

            if not username_val:
                return JsonResponse({"message": "토큰 내부 정보가 올바르지 않습니다."}, status=401)

            # 🚀 [교정] 존재하지 않는 id 조회는 아예 코드를 삭제하고 오직 username으로만 타격합니다.
            request.user = User.objects.get(username=str(username_val).strip())

        except User.DoesNotExist:
            return JsonResponse({"message": "유효하지 않은 토큰이거나 존재하지 않는 유저입니다."}, status=401)
        except Exception as e:
            # 💡 혹시라도 터지면 콘솔에서 무슨 에러인지 정확히 단어를 보려고 추가한 방어선
            print(f"🚨 [데코레이터 최종 예외 로그]: {str(e)}")
            return JsonResponse({"message": f"인증 처리 오류: {str(e)}"}, status=500)

        return func(request, *args, **kwargs)

    return wrapper