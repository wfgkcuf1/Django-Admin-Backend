"""
用户认证路由 — 登录/注册/Token。

知识点:
  - 使用 namespace 避免 URL 冲突
  - simplejwt 提供的 TokenRefreshView
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, RegisterView

app_name = "auth"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
