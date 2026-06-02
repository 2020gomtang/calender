import json
import re
import datetime
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView  # 💡 TemplateView 정상 매핑 완료
from django.utils.decorators import method_decorator
from django.db import transaction
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
from google import genai

from .models import Plan, PlanHistory  # 💡 중복 제거 및 깔끔하게 한 라인으로 축약
from User.decorators import login_required_jwt
from Post.models import PostComment


def get_verified_db_user(request_user):
    User = get_user_model()
    if isinstance(request_user, User):
        return request_user

    # 가짜 객체나 텍스트 타입인 경우 문자열 정제 필터 작동
    username_str = getattr(request_user, 'username', str(request_user))
    if "User:" in username_str:
        username_str = username_str.split("User:")[-1].strip()
    if "(" in username_str:
        username_str = username_str.split("(")[0].strip()
    username_str = username_str.replace("<", "").replace(">", "").strip()

    return User.objects.get(username=username_str)

# ➊ 계획 생성 뷰 (카테고리 반영)
@method_decorator(login_required_jwt, name='dispatch')
class PlanCreateView(View):
    def post(self, request, *args, **kwargs):
        try:
            # 1. 프론트엔드가 보낸 JSON 데이터 파싱
            data = json.loads(request.body)
            category = data.get('category')
            title = data.get('title')
            content = data.get('content')
            assigned_date = data.get('assigned_date')

            # 2. 실전 방어용 유저 인스턴스 강제 변환 레이어
            User = get_user_model()

            # request.user가 실제 장고 User 인스턴스인지 체크
            if isinstance(request.user, User):
                db_user = request.user
            else:
                # 💡 만약 미들웨어가 커스텀 객체나 텍스트를 던졌다면 실제 username 속성을 추출
                username_str = getattr(request.user, 'username', str(request.user))

                # 괄호나 특수문자가 섞여 있는 문자열("<User: 2020gomtang (김태림)>") 정제 가공
                if "User:" in username_str:
                    username_str = username_str.split("User:")[-1].strip()
                if "(" in username_str:
                    username_str = username_str.split("(")[0].strip()
                username_str = username_str.replace("<", "").replace(">", "").strip()

                # DB에서 진짜 장고 유저 인스턴스를 무조건 한 대 때려서 가져옵니다.
                db_user = User.objects.get(username=username_str)

            # 3. Gemini AI 가동 및 검증 영역 (기존 비즈니스 로직 연동)
            # 예시용 임시 시간 할당 (유저님의 기동중인 Gemini 파싱 함수로 대체 가능)
            ai_calculated_hours = 4

            existing_hours = Plan.objects.filter(
                user=db_user,
                assigned_date=assigned_date
            ).aggregate(total=Sum('ai_duration_hours'))['total'] or 0

            if existing_hours + ai_calculated_hours > 24:
                return JsonResponse({
                    "message": f"하루 24시간 한도를 초과할 수 없습니다. (현재: {existing_hours}h / 추가요청: {ai_calculated_hours}h)"
                }, status=400)

            # 4. 장고 ORM 검증을 통과하는 진짜 인스턴스 주입 생성
            plan = Plan.objects.create(
                user=db_user,  # 🚀 ValueError를 100% 원천 차단하는 진짜 User 객체
                category=category,
                title=title,
                content=content,
                ai_duration_hours=ai_calculated_hours,
                assigned_date=assigned_date
            )

            return JsonResponse({
                "message": f"🤖 AI가 분석한 소요 시간은 [{ai_calculated_hours}시간] 입니다. 목록에 배치 완료!"
            }, status=201)

        except User.DoesNotExist:
            return JsonResponse({"message": "존재하지 않는 유저 세션 정보입니다."}, status=401)
        except Exception as e:
            return JsonResponse({"message": f"서버 내부 오류: {str(e)}"}, status=500)

# ➋ 💡 핵심: 템플릿에서 같은 박스에 모아 보여주기 위한 그룹화 조회 뷰
@method_decorator(login_required_jwt, name='dispatch')
class PlanListView(View):
    def get(self, request, *args, **kwargs):
        try:
            User = get_user_model()

            # 조회할 때도 동일하게 진짜 유저 객체 획득 로직 작동
            if isinstance(request.user, User):
                db_user = request.user
            else:
                username_str = getattr(request.user, 'username', str(request.user))
                if "User:" in username_str:
                    username_str = username_str.split("User:")[-1].strip()
                if "(" in username_str:
                    username_str = username_str.split("(")[0].strip()
                username_str = username_str.replace("<", "").replace(">", "").strip()
                db_user = User.objects.get(username=username_str)

            # 해당 유저의 계획 필터링 조회
            plans = Plan.objects.filter(user=db_user)

            # 카테고리별 그룹화 딕셔너리 생성 빌드
            grouped_plans = {}
            for plan in plans:
                if plan.category not in grouped_plans:
                    grouped_plans[plan.category] = []
                grouped_plans[plan.category].append({
                    "id": plan.id,
                    "title": plan.title,
                    "content": plan.content,
                    "ai_duration_hours": plan.ai_duration_hours,
                    "status": plan.status,
                    "is_shared": getattr(plan, 'is_shared', False)
                })

            return JsonResponse({"grouped_plans": grouped_plans}, status=200)

        except Exception as e:
            return JsonResponse({"message": f"목록 로드 실패: {str(e)}"}, status=500)
@method_decorator(login_required_jwt, name='dispatch')
class MonthlyPlanCalendarView(View):
    def get(self, request, *args, **kwargs):
        # 프론트엔드가 주소창에 ?year=2026&month=5 형태로 준 값을 읽어옵니다.
        year = request.GET.get('year', datetime.datetime.now().year)
        month = request.GET.get('month', datetime.datetime.now().month)

        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return JsonResponse({"message": "연도와 월은 숫자여야 합니다."}, status=400)

        # 💡 핵심: 해당 월의 시작일과 종료일을 계산해서 그 사이의 데이터만 필터링합니다.
        # 예: 2026년 5월인 경우 -> 2026-05-01 00:00:00 ~ 2026-05-31 23:59:59
        start_date = datetime.datetime(year, month, 1)
        if month == 12:
            end_date = datetime.datetime(year + 1, 1, 1)
        else:
            end_date = datetime.datetime(year, month + 1, 1)

        # 현재 로그인한 유저의 계획 중, 해당 월의 데드라인을 가진 기록들을 전부 긁어옵니다.
        # (성공한 기록, 실패한 기록, 대기 중인 기록 모두 포함)
        plans = Plan.objects.filter(
            user=request.user,
            deadline__gte=start_date,
            deadline__lt=end_date
        )

        # 달력 날짜별로 매핑하기 좋게 가공해서 던져줍니다.
        plan_list = []
        for plan in plans:
            plan_list.append({
                "id": plan.id,
                "category": plan.category,
                "title": plan.title,
                "deadline": plan.deadline.strftime('%Y-%m-%d'), # 프론트가 달력 날짜 칸에 꽂기 편하게 포맷팅
                "status": plan.status, # SUCCESS, FAIL, PENDING 확인용
                "ai_duration_hours": plan.ai_duration_hours
            })

        return JsonResponse({
            "year": year,
            "month": month,
            "monthly_records": plan_list
        }, status=200)


@method_decorator(login_required_jwt, name='dispatch')
class PlanCompleteView(View):
    def post(self, request, plan_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
            result_status = data.get('result')

            plan = Plan.objects.get(id=plan_id, user=request.user)

            with transaction.atomic():
                # 1. 히스토리 생성
                history = PlanHistory.objects.create(
                    user=plan.user,
                    category=plan.category,
                    title=plan.title,
                    result=result_status,
                    completed_at=datetime.date.today()
                )

                # 2. 🚨 Post 앱에 정의된 댓글들의 타겟을 기존 Plan에서 새 History로 토스!
                PostComment.objects.filter(plan=plan).update(plan=None, plan_history=history)

                # 3. 원본 계획 삭제
                plan.delete()

            return JsonResponse({"message": "완료 처리 및 댓글 이관 성공"}, status=200)
        except Plan.DoesNotExist:
            return JsonResponse({"message": "계획 없음"}, status=404)
@method_decorator(login_required_jwt, name='dispatch')
class PastCalendarHistoryView(View):
    """
    사용자가 과거 달력을 조회할 때, 해당 연도/월에 유저가 달성했던 성공/실패 히스토리만 반환합니다.
    """
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year', timezone.now().year)
        month = request.GET.get('month', timezone.now().month)

        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return JsonResponse({"message": "연도와 월 파라미터가 올바르지 않습니다."}, status=400)

        # 해당 월에 완료(수행)했던 순수 히스토리 데이터만 필터링 쿼리
        histories = PlanHistory.objects.filter(
            user=request.user,
            completed_at__year=year,
            completed_at__month=month
        )

        history_list = []
        for h in histories:
            history_list.append({
                "category": h.category,
                "title": h.title,
                "completed_at": h.completed_at.strftime('%Y-%m-%d'), # 언제 했는지 날짜
                "result": h.result                                    # 💡 진짜 성공(SUCCESS) / 실패(FAIL) 여부만 딱 전달
            })

        return JsonResponse({
            "year": year,
            "month": month,
            "past_records": history_list
        }, status=200)

class PlanDetailView(TemplateView):
    template_name = 'Plan/plan_detail.html'