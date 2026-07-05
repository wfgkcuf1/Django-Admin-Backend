"""
用户管理路由 — 用户 CRUD 操作。

知识点:
  - DefaultRouter: 自动生成标准路由
  - routing.py 模式（把路由从 views.py 中分离）
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet

app_name = "users"

# 知识点: DefaultRouter 自动生成
#   /users/         → list (GET)
#   /users/         → create (POST)
#   /users/{id}/    → retrieve (GET)
#   /users/{id}/    → update (PUT)
#   /users/{id}/    → partial_update (PATCH)
#   /users/{id}/    → destroy (DELETE)
router = DefaultRouter()
router.register("", UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
]
