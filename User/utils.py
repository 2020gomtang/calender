# User/utils.py
import jwt
import datetime
from django.conf import settings
from .models import User


# 토큰 발급 함수 (Access Token)
def generate_access_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        # 토큰 만료 시간 설정 (예: 발급 후 2시간 동안 유효)
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2),
        # 토큰 발급 시간
        'iat': datetime.datetime.utcnow()
    }

    # settings.SECRET_KEY를 암호화 키로 사용하여 JWT 생성
    access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return access_token


# 토큰 검증 함수
def validate_token(token):
    try:
        # 토큰 디코딩 (만료 시간 자동 검증 포함)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        # 토큰 만료 에러
        return None
    except jwt.InvalidTokenError:
        # 잘못된 토큰 에러
        return None