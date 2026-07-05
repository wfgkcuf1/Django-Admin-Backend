from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.base_view import BaseViewSet
from common.response import ok, created
from .models import UploadedFile
from .serializers import FileListSerializer, FileUploadSerializer


class FileViewSet(BaseViewSet):
    queryset = UploadedFile.objects.filter(deleted_at__isnull=True)
    serializer_class = FileListSerializer
    search_fields = ["original_name"]
    ordering = "-created_at"

    # 文件上传需要 MultiPartParser
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.save()
        return created(
            data=FileListSerializer(file_obj).data,
            message="文件上传成功",
        )

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser])
    def multi_upload(self, request):
        """批量上传。"""
        files = request.FILES.getlist("files")
        results = []
        for file in files:
            file_obj = UploadedFile.objects.create(
                original_name=file.name,
                file=file,
                created_by=request.user,
            )
            results.append(FileListSerializer(file_obj).data)

        return ok(data=results, message=f"成功上传 {len(results)} 个文件")
