from rest_framework import serializers
from common.base_serializer import BaseModelSerializer
from .models import OperationLog


class OperationLogSerializer(BaseModelSerializer):
    class Meta:
        model = OperationLog
        fields = "__all__"
        read_only_fields = "__all__"
