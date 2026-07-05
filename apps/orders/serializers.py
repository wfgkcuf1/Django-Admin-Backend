from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from common.base_serializer import BaseModelSerializer
from common.enums import OrderStatus
from .models import Order, OrderItem, PaymentLog


class OrderItemSerializer(BaseModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class PaymentLogSerializer(BaseModelSerializer):
    class Meta:
        model = PaymentLog
        fields = "__all__"


class OrderListSerializer(BaseModelSerializer):
    user_name = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    def get_user_name(self, obj):
        return obj.user.display_name if obj.user else ""

    def get_status_label(self, obj):
        try:
            return OrderStatus(obj.status).name
        except ValueError:
            return obj.status


class OrderCreateSerializer(BaseModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["items", "remark"]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("订单项不能为空")
        return items

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        validated_data["user"] = self.context["request"].user

        order = Order.objects.create(**validated_data)
        total = Decimal("0.00")

        for item_data in items_data:
            item = OrderItem.objects.create(order=order, **item_data)
            total += item.subtotal

        order.total_amount = total
        order.pay_amount = total
        order.save(update_fields=["total_amount", "pay_amount"])

        return order
