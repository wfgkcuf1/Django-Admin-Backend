from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet

app_name = "files"

router = DefaultRouter()
router.register("", FileViewSet, basename="files")

urlpatterns = [path("", include(router.urls))]
