# Post/urls.py 전체 코드

from django.urls import path
from .views import (
    PostBoardView,
    PostCommentCreateView,
    DeleteCommentView,
    ToggleShareView,
    PostShareToggleView
)

app_name = 'post'

urlpatterns = [
    # 📮 게시판 메인 피드 조회 엔드포인트 (/api/post/board/)
    path('board/', PostBoardView.as_view(), name='board_main'),

    # 💬 [404 해결사] 댓글 생성 엔드포인트 (/api/post/comment/create/)
    path('comment/create/', PostCommentCreateView.as_view(), name='comment_create'),

    # ❌ 댓글 삭제 엔드포인트 (/api/post/comment/delete/<int:comment_id>/)
    path('comment/delete/<int:comment_id>/', DeleteCommentView.as_view(), name='comment_delete'),

    # 🔒 플래너 화면용 토글 엔드포인트 (/api/post/share/toggle/)
    path('share/toggle/', PostShareToggleView.as_view(), name='share_toggle'),
]