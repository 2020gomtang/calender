# User/urls.py
from django.urls import path
from User.views import SignUpView, LoginView, MainWorkspaceView


urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('main/', MainWorkspaceView.as_view(), name='main_workspace'),

]