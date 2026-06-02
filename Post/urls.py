# Post/urls.py
from django.urls import path
from .views import PostBoardView, PostCommentCreateView

urlpatterns = [
    # 브라우저 화면 서빙 및 데이터 API 통합 엔드포인트
    path('board/', PostBoardView.as_view(), name='board_main_page'),

    # 댓글 등록 전용 API 패스
    path('comment/', PostCommentCreateView.as_view(), name='post_comment_create'),
]