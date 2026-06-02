# User/urls.py
from django.urls import path
from .views import MainWorkspaceView, SignUpView, LoginView, UserFriendView  # 🚀 UserFriendView 추가 임포트!

urlpatterns = [
    path('main/', MainWorkspaceView.as_view(), name='main'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),

    # 🚀 [대통합 주소 라인]
    # 이제 이 주소 하나가 화면 서빙, 목록 스캔, 친구 추가/삭제까지 올인원으로 제어합니다!
    path('friend/', UserFriendView.as_view(), name='user_friend_manage'),
]