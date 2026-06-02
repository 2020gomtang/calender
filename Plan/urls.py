# Plan/urls.py
from django.urls import path
from .views import (
    PlanCreateView,
    PlanListView,
    MonthlyPlanCalendarView,
    PlanCompleteView,       # 🚨 이 녀석이 빠져있었을 겁니다! 확실히 추가해 주세요.
    PastCalendarHistoryView,
    PlanDetailView
)

urlpatterns = [
    path('create/', PlanCreateView.as_view(), name='plan_create'),
    path('list/', PlanListView.as_view(), name='plan_list'),
    path('complete/<int:plan_id>/', PlanCompleteView.as_view(), name='plan_complete'),
    path('history/', PastCalendarHistoryView.as_view(), name='past_calendar_history'),

    # 💡 상세 계획 구성 모듈 화면 진입 주소 확보
    path('detail/', PlanDetailView.as_view(), name='plan_detail_page'),
]

