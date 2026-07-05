from rest_framework import serializers
from common.base_serializer import BaseModelSerializer
from common.enums import FileType
from .models import UploadedFile


class FileListSerializer(BaseModelSerializer):
    url = serializers.URLField(read_only=True)
    size_display = serializers.CharField(read_only=True)

    class Meta:
        model = UploadedFile
        fields = "__all__"


class FileUploadSerializer(serializers.Serializer):
    """文件上传序列化器（非 ModelSerializer）。"""
    file = serializers.FileField()
    file_type = serializers.ChoiceField(
        choices=[(f.value, f.name) for f in FileType],
        required=False,
    )

    def validate_file(self, value):
        from common.constants import MAX_FILE_SIZE_MB
        if value.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"文件大小不能超过 {MAX_FILE_SIZE_MB}MB"
            )
        return value

    def create(self, validated_data):
        return UploadedFile.objects.create(
            original_name=validated_data["file"].name,
            file=validated_data["file"],
            file_type=validated_data.get("file_type", FileType.OTHER.value),
            created_by=self.context["request"].user,
        )
