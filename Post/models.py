# Post/models.py
from django.db import models
from django.conf import settings


class PostComment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_comments',
        verbose_name="댓글 작성자"
    )

    # 💡 Plan의 모델들을 외래키로 참조하되, Post 앱의 소속으로 분리합니다.
    plan = models.ForeignKey(
        'Plan.Plan',
        on_delete=models.CASCADE,
        related_name='post_comments',
        null=True,
        blank=True,
        verbose_name="연동된 진행중 계획"
    )

    plan_history = models.ForeignKey(
        'Plan.PlanHistory',
        on_delete=models.CASCADE,
        related_name='post_comments',
        null=True,
        blank=True,
        verbose_name="연동된 완료 기록"
    )

    content = models.TextField(verbose_name="댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="댓글 작성일")

    class Meta:
        db_table = 'post_comments'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.user.username}] {self.content[:15]}"