from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperationLogViewSet

app_name = "logs"

router = DefaultRouter()
router.register("", OperationLogViewSet, basename="logs")

urlpatterns = [path("", include(router.urls))]
