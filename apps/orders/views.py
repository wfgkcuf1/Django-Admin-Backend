from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.base_view import BaseViewSet
from common.response import ok, fail
from .models import Order
from .serializers import OrderListSerializer, OrderCreateSerializer


class OrderViewSet(BaseViewSet):
    queryset = Order.objects.filter(deleted_at__isnull=True)
    search_fields = ["order_no", "user__username"]
    ordering_fields = ["created_at", "total_amount", "pay_amount"]
    ordering = "-created_at"

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        return self.queryset.filter(user=user)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        order = self.get_object()
        try:
            order.pay()
            return ok(message="支付成功")
        except ValueError as e:
            return fail(message=str(e))

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = self.get_object()
        try:
            order.complete()
            return ok(message="订单已完成")
        except ValueError as e:
            return fail(message=str(e))

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        reason = request.data.get("reason", "")
        try:
            order.cancel(reason)
            return ok(message="订单已取消")
        except ValueError as e:
            return fail(message=str(e))
