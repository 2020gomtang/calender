from django.http import JsonResponse
from .utils import validate_token
from .models import User  # 유저님이 보여주신 커스텀 User 모델 테이블


def login_required_jwt(func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', None)

        if not auth_header:
            print("🚨 [JWT 최종 디버깅] 헤더에 Authorization 키 자체가 없습니다!")
            return JsonResponse({"message": "토큰이 제공되지 않았습니다."}, status=401)

        try:
            prefix, token = auth_header.split(' ')
            if prefix != 'Bearer':
                print(f"🚨 [JWT 최종 디버깅] Bearer 접두사가 없습니다. 들어온 값: {prefix}")
                return JsonResponse({"message": "토큰 형식이 올바르지 않습니다."}, status=401)

            # 1. 토큰 복호화 시도
            payload = validate_token(token)

            if not payload:
                # 💡 만약 validate_token 내부에서 오류가 나서 None이 반환되면 여기가 찍힙니다.
                print(f"🚨 [JWT 최종 디버깅] validate_token(token) 결과가 None입니다! 토큰 검증(비밀키/만료일) 실패. 토큰값: {token[:20]}...")
                return JsonResponse({"message": "토큰이 만료되었거나 유효하지 않습니다."}, status=401)

            print(f"🕵️‍♂️ [JWT 최종 디버깅] 토큰 복호화 대성공! 페이로드 내용물: {payload}")

            # 2. 페이로드 내부의 모든 키 조합 테스트 추출
            # 로그인 뷰가 user_id로 구웠든, id로 구웠든, username으로 구웠든 다 끄집어냅니다.
            user_identity = payload.get('username') or payload.get('user_id') or payload.get('id')
            print(f"🔎 [JWT 최종 디버깅] 페이로드에서 추출한 유저 식별자 키값: '{user_identity}'")

            if not user_identity:
                print("🚨 [JWT 최종 디버깅] 페이로드 안에 username이나 user_id 관련 키가 아예 없습니다!")
                return JsonResponse({"message": "토큰 내부 정보가 올바르지 않습니다."}, status=401)

            # 3. 데이터베이스 조회 (식별자가 숫자형태면 id로, 문자 형태면 username으로 가변 타격)
            if str(user_identity).isdigit():
                print(f"⚡ [JWT 최종 디버깅] 식별자가 숫자이므로 id={user_identity} 조회를 시도합니다.")
                request.user = User.objects.get(id=int(user_identity))
            else:
                print(f"⚡ [JWT 최종 디버깅] 식별자가 문자열이므로 username='{user_identity}' 조회를 시도합니다.")
                request.user = User.objects.get(username=str(user_identity))

            print(f"🎉 [JWT 최종 디버깅] DB에서 유저 매핑 성공! request.user -> {request.user}")

        except User.DoesNotExist:
            print(f"🚨 [JWT 최종 디버깅] DB 조회 실패: 테이블에 '{user_identity}'에 매칭되는 유저가 진짜 없습니다!")
            return JsonResponse({"message": "유효하지 않은 토큰이거나 존재하지 않는 유저입니다."}, status=401)
        except Exception as e:
            print(f"🚨 [JWT 최종 디버깅] 예상치 못한 시스템 런타임 에러 발생: {str(e)}")
            return JsonResponse({"message": "인증 처리 중 서버 내부 오류"}, status=401)

        return func(request, *args, **kwargs)

    return wrapper