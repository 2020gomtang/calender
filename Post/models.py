# Post/models.py
from django.db import models
from django.conf import settings


class Post(models.Model):
    # User 앱 참조
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="작성자"
    )

    # Plan 앱의 Plan 모델을 'Plan.Plan' 문자열로 참조 (순환 참조 방지 핵심!)
    plan = models.ForeignKey(
        'Plan.Plan',
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name="연관된 계획"
    )
    content = models.TextField(verbose_name="게시글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")

    class Meta:
        db_table = 'posts'

    def __str__(self):
        return f"게시글 {self.id} (작성자: {self.user.username})"