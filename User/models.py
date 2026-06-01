# User/models.py
from django.db import models


class User(models.Model):
    # 1. 아이디 (로그인할 때 쓰는 ID)
    username = models.CharField(
        max_length=50,
        unique=True,  # 중복 아이디 방지
        verbose_name="아이디"
    )

    # 2. 비밀번호 (실제 서비스에서는 해시 암호화해서 저장해야 합니다)
    password = models.CharField(
        max_length=128,
        verbose_name="비밀번호"
    )

    # 3. 이메일
    email = models.EmailField(
        max_length=254,
        unique=True,  # 중복 이메일 방지
        verbose_name="이메일"
    )

    # 4. 이름
    name = models.CharField(
        max_length=50,
        verbose_name="이름"
    )

    # 생성일 (언제 가입했는지 알면 좋으니 기본으로 넣어둡니다)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="가입일"
    )

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.name})"