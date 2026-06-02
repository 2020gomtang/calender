# Post/models.py 전체 마감본

from django.db import models

class PostComment(models.Model):
    # 🚀 [대수술] settings 의존성을 버리고 유저님의 진짜 커스텀 User 모델을 직접 조준합니다.
    # 또한 다른 테이블들과 완벽하게 규격을 맞추기 위해 to_field와 db_column을 명시합니다.
    user = models.ForeignKey(
        'User.User',                  # 🎯 유저님이 만든 users 테이블로 직접 조준!
        on_delete=models.CASCADE,
        to_field='username',          # 🎯 숫자 ID 대신 username 문자열을 외래키로 바인딩!
        db_column='user_username',    # 🎯 DB 컬럼명도 직관적으로 고정
        related_name='post_comments',
        verbose_name="댓글 작성자"
    )

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
        return f"[{self.user_username}] {self.content[:15]}"