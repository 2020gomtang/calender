from django.db import models

class User(models.Model):
    # 1. 아이디 (로그인할 때 쓰는 ID)
    username = models.CharField(
        max_length=50,
        unique=True,  # 중복 아이디 방지
        verbose_name="아이디"
    )

    # 2. 비밀번호
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

    # 생성일
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="가입일"
    )

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.name})"


# 🚀 [대통합] Friend 모델을 User 앱 내부로 흡수 완료!
class Friend(models.Model):
    # ⚡ 유저님 원본 설계 구조를 그대로 유지하며 같은 앱 내부 참조로 전환
    from_user = models.ForeignKey(
        'User',  # 🚀 같은 앱 내에 있으므로 문자열로 완벽히 직통 연결됩니다.
        on_delete=models.CASCADE,
        to_field='username',
        db_column='from_user_username',
        related_name='from_users',
        verbose_name="나"
    )

    to_user = models.ForeignKey(
        'User',  # 🚀 같은 앱 내에 있으므로 문자열로 완벽히 직통 연결됩니다.
        on_delete=models.CASCADE,
        to_field='username',
        db_column='to_user_username',
        related_name='to_users',
        verbose_name="친구"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="친구 맺은 날짜")

    class Meta:
        db_table = 'friends'
        constraints = [
            # 동일한 친구 관계가 중복으로 생성되는 것을 디비 레벨에서 원천 차단 (idempotency 보장)
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friendship')
        ]

    def __str__(self):
        return f"{self.from_user.username} 🤝 {self.to_user.username}"