# Plan/models.py
from django.db import models
from django.conf import settings


class Plan(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', '대기'
        SUCCESS = 'SUCCESS', '성공'
        FAIL = 'FAIL', '실패'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plans')
    category = models.CharField(max_length=100, verbose_name="큰 분류 (카테고리)", default="기타")
    title = models.CharField(max_length=255, verbose_name="계획 이름")
    content = models.TextField(blank=True, null=True, verbose_name="계획 내용")

    # 💡 추가: 사용자가 달력에서 드래그 앤 드롭 하거나 지정한 "실제 계획 수행 날짜"
    assigned_date = models.DateField(blank=True, null=True, verbose_name="계획 배치 날짜")

    deadline = models.DateTimeField(blank=True, null=True, verbose_name="사용자 설정 데드라인")
    ai_duration_hours = models.PositiveIntegerField(blank=True, null=True, verbose_name="AI 예측 소요 시간(시간)", default=0)

    # 💡 대기/성공/실패를 여기서도 제어할 수 있도록 상태 유지
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name="상태"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'plans'


# Plan/models.py 맨 밑에 추가

class PlanHistory(models.Model):
    class ResultChoices(models.TextChoices):
        SUCCESS = 'SUCCESS', '성공'
        FAIL = 'FAIL', '실패'

    # 어떤 유저의 과거 기록인지 식별
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plan_histories',
        verbose_name="작성자"
    )

    # 달력에 박스별로 묶어주기 위해 기존 카테고리 명칭 보존
    category = models.CharField(max_length=100, verbose_name="큰 분류 (카테고리)")
    title = models.CharField(max_length=255, verbose_name="계획 이름")

    # 💡 핵심: 사용자가 이 계획을 '실제로 완료(수행)한 날짜'
    completed_at = models.DateField(verbose_name="실제 수행일")

    # 💡 핵심: 진짜 성공했는지 실패했는지 여부만 딱 저장 (SUCCESS / FAIL)
    result = models.CharField(
        max_length=10,
        choices=ResultChoices.choices,
        verbose_name="성공 여부"
    )

    class Meta:
        db_table = 'plan_histories'
        # 관리를 편하게 하기 위해 최신 기록 순으로 정렬 설정
        ordering = ['-completed_at']

    def __str__(self):
        return f"[{self.completed_at}] ({self.get_result_display()}) {self.title}"
