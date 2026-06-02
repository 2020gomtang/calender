import json
import re
import datetime
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.db import transaction
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.db.models import Sum
from django.utils import timezone

from .models import Plan, PlanHistory
from User.decorators import login_required_jwt
from Post.models import PostComment


# ➊ 계획 생성 뷰 (공유 초기 상태 필드 완전 확보)
@method_decorator(login_required_jwt, name='dispatch')
class PlanCreateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            category = data.get('category')
            title = data.get('title')
            content = data.get('content')
            assigned_date = data.get('assigned_date')

            db_user = request.user
            u_name = db_user.username

            ai_calculated_hours = 4

            # 24시간 한도 체크
            existing_hours = Plan.objects.filter(
                user__username=u_name,
                assigned_date=assigned_date
            ).aggregate(total=Sum('ai_duration_hours'))['total'] or 0

            if existing_hours + ai_calculated_hours > 24:
                return JsonResponse({
                    "message": f"하루 24시간 한도를 초과할 수 없습니다. (현재: {existing_hours}h)"
                }, status=400)

            # 🚀 [교정] 생성할 때 'is_shared=False'를 명시적으로 때려 박아
            # 나만보기 🔒 상태에서 토글 대기하도록 구조를 고정합니다.
            plan = Plan.objects.create(
                user=db_user,
                category=category,
                title=title,
                content=content,
                ai_duration_hours=ai_calculated_hours,
                assigned_date=assigned_date,
                is_shared=False  # 🚀 명시적 초기화 조치!
            )

            return JsonResponse({
                "message": f"🤖 AI가 분석한 소요 시간은 [{ai_calculated_hours}시간] 입니다. 목록에 배치 완료!"
            }, status=201)

        except Exception as e:
            return JsonResponse({"message": f"서버 내부 오류: {str(e)}"}, status=500)


# ➋ 템플릿 그룹화 조회 뷰 (is_shared 데이터 필드 정밀 동기화)
@method_decorator(login_required_jwt, name='dispatch')
class PlanListView(View):
    def get(self, request, *args, **kwargs):
        try:
            db_user = request.user
            u_name = db_user.username

            # 🚀 user__username 필터링으로 내 계획 데이터 명확히 획득
            plans = Plan.objects.filter(user__username=u_name)

            grouped_plans = {}
            for plan in plans:
                if plan.category not in grouped_plans:
                    grouped_plans[plan.category] = []

                # 🚀 [긴급 조치] 모델 필드 오차 검증 및 안전한 형변환
                # DB 마이그레이션 상태에 따라 1/0 혹은 True/False로 들어오는 값을
                # 프론트엔드가 정확히 판별할 수 있도록 순수 불리언(True/False)으로 강제 컨버전합니다.
                raw_shared = getattr(plan, 'is_shared', None)
                if raw_shared is None:
                    # 만약 모델에 필드가 아예 없어서 getattr이 None을 뱉는 최악의 상황이라면
                    # 임시방편으로 False 처리하되, 실제 모델에 'is_shared = models.BooleanField(default=False)'가 있는지 꼭 확인하셔야 합니다!
                    is_shared_status = False
                else:
                    is_shared_status = bool(raw_shared)

                grouped_plans[plan.category].append({
                    "id": plan.id,
                    "title": plan.title,
                    "content": plan.content,
                    "ai_duration_hours": plan.ai_duration_hours,
                    "status": plan.status,
                    "is_shared": is_shared_status  # 🚀 프론트 자바스크립트가 읽어갈 확실한 마스터 키
                })

            return JsonResponse({"grouped_plans": grouped_plans}, status=200)

        except Exception as e:
            return JsonResponse({"message": f"목록 로드 실패: {str(e)}"}, status=500)


# ➌ 월별 달력 범위 쿼리 뷰
@method_decorator(login_required_jwt, name='dispatch')
class MonthlyPlanCalendarView(View):
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year', datetime.datetime.now().year)
        month = request.GET.get('month', datetime.datetime.now().month)

        try:
            year, month = int(year), int(month)
        except ValueError:
            return JsonResponse({"message": "연도와 월은 숫자여야 합니다."}, status=400)

        start_date = datetime.datetime(year, month, 1)
        end_date = datetime.datetime(year + 1, 1, 1) if month == 12 else datetime.datetime(year, month + 1, 1)

        db_user = request.user
        plans = Plan.objects.filter(
            user__username=db_user.username,
            deadline__gte=start_date,
            deadline__lt=end_date
        )

        plan_list = []
        for plan in plans:
            plan_list.append({
                "id": plan.id,
                "category": plan.category,
                "title": plan.title,
                "deadline": plan.deadline.strftime('%Y-%m-%d') if plan.deadline else None,
                "status": plan.status,
                "ai_duration_hours": plan.ai_duration_hours
            })

        return JsonResponse({"year": year, "month": month, "monthly_records": plan_list}, status=200)


# ➍ 계획 완료 및 히스토리 이관 트랜잭션 뷰 (공유 유실 방지 수리)
@method_decorator(login_required_jwt, name='dispatch')
class PlanCompleteView(View):
    def post(self, request, plan_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
            result_status = data.get('result')

            db_user = request.user
            plan = Plan.objects.get(id=plan_id, user__username=db_user.username)

            with transaction.atomic():
                # 🚀 [보정] 완료 이관 시 계획에 세팅되어 있던 공유 여부 상태(is_shared)를
                # 히스토리 보관함 테이블에도 그대로 승계시켜 이관합니다.
                history = PlanHistory.objects.create(
                    user=plan.user,
                    category=plan.category,
                    title=plan.title,
                    result=result_status,
                    is_shared=bool(getattr(plan, 'is_shared', False)),  # 🚀 공유 상태 그대로 이관
                    completed_at=datetime.date.today()
                )
                PostComment.objects.filter(plan=plan).update(plan=None, plan_history=history)
                plan.delete()

            return JsonResponse({"message": "완료 처리 및 댓글 이관 성공"}, status=200)
        except Plan.DoesNotExist:
            return JsonResponse({"message": "계획 없음"}, status=404)
        except Exception as e:
            return JsonResponse({"message": f"서버 오류: {str(e)}"}, status=500)


# ➎ 과거 수행 이력 조회 뷰
@method_decorator(login_required_jwt, name='dispatch')
class PastCalendarHistoryView(View):
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year', timezone.now().year)
        month = request.GET.get('month', timezone.now().month)

        try:
            year, month = int(year), int(month)
        except ValueError:
            return JsonResponse({"message": "파라미터 오류"}, status=400)

        db_user = request.user
        histories = PlanHistory.objects.filter(
            user__username=db_user.username,
            completed_at__year=year,
            completed_at__month=month
        )

        history_list = []
        for h in histories:
            history_list.append({
                "category": h.category,
                "title": h.title,
                "completed_at": h.completed_at.strftime('%Y-%m-%d'),
                "result": h.result,
                "is_shared": bool(getattr(h, 'is_shared', False))
            })

        return JsonResponse({"year": year, "month": month, "past_records": history_list}, status=200)


# ➏ 상세 템플릿 페이지 렌더링 뷰
class PlanDetailView(TemplateView):
    template_name = 'Plan/plan_detail.html'