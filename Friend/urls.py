# Friend/urls.py
from django.urls import path
from .views import FriendView

urlpatterns = [
    # 단일 클래스 내부에서 GET(화면+목록), POST(추가), DELETE(삭제)를 다 처리하는 실전형 URL 아키텍처
    path('manage/', FriendView.as_view(), name='friend_management'),
]