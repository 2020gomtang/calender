# Plan/models.py
from django.db import models
from django.conf import settings

class Plan(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', '대기'
        SUCCESS = 'SUCCESS', '성공'
        FAIL = 'FAIL', '실패'

    # settings를 통해 User 앱의 유저 모델을 안전하게 참조합니다.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plans',
        verbose_name="작성자"
    )
    title = models.CharField(max_length=255, verbose_name="계획 이름")
    content = models.TextField(blank=True, null=True, verbose_name="계획 내용")
    deadline = models.DateTimeField(verbose_name="데드라인")
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name="상태"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:

        db_table = 'plans'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"