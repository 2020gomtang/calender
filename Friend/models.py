# Friend/models.py
from django.db import models
from django.conf import settings

class Friend(models.Model):
    # 나에게 친구를 추가한 주체 유저
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='from_users',
        verbose_name="나"
    )
    # 내가 추가한 상대방 유저
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='to_users',
        verbose_name="친구"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="친구 맺은 날짜")

    class Meta:
        db_table = 'friends'
        # 💡 constraints 로 수정해 줍니다! (배열 안에 UniqueConstraint를 넣는 식입니다)
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friendship')
        ]

    def __str__(self):
        return f"{self.from_user.username} 🤝 {self.to_user.username}"