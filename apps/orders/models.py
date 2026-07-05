"""
订单管理模型 — 订单 + 订单项 + 支付记录。

知识点:
  1. DecimalField: 精确金额
  2. F() 表达式: 字段级原子操作
  3. Q() 表达式: 复杂查询条件
  4. @transaction.atomic: 事务保证
  5. 状态机模式: 订单状态流转
"""
import uuid
from decimal import Decimal
from typing import Optional

from django.db import models, transaction
from django.db.models import F, Q

from common.base_model import BaseModel, TimestampMixin
from common.enums import OrderStatus


class Order(BaseModel):
    """
    订单模型。

    知识点:
      - DecimalField: 精确小数，max_digits=10, decimal_places=2
      - 订单编号手动生成而非用 UUID
    """
    # 订单号 — 自定义编号策略
    order_no = models.CharField(
        verbose_name="订单号",
        max_length=32,
        unique=True,
        db_index=True,
    )
    total_amount = models.DecimalField(
        verbose_name="总金额",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    discount_amount = models.DecimalField(
        verbose_name="折扣金额",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    pay_amount = models.DecimalField(
        verbose_name="实付金额",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    status = models.CharField(
        verbose_name="订单状态",
        max_length=20,
        choices=[(s.value, s.name) for s in OrderStatus],
        default=OrderStatus.PENDING.value,
        db_index=True,
    )
    paid_at = models.DateTimeField(verbose_name="支付时间", null=True, blank=True)

    # 关联
    user = models.ForeignKey(
        "users.User",
        verbose_name="用户",
        on_delete=models.CASCADE,
        related_name="orders",
    )

    class Meta:
        db_table = "biz_order"
        verbose_name = "订单"
        verbose_name_plural = "订单列表"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.order_no

    def save(self, *args, **kwargs) -> None:
        """创建时自动生成订单号。"""
        if not self.order_no:
            self.order_no = self._generate_order_no()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_no() -> str:
        """生成订单号: 年月日+随机6位。"""
        from datetime import datetime
        import random
        date_part = datetime.now().strftime("%Y%m%d%H%M%S")
        rand_part = str(random.randint(100000, 999999))
        return f"ORD{date_part}{rand_part}"

    @transaction.atomic
    def pay(self, payment_method: str = "wechat") -> "Order":
        """
        支付 — 状态机流转。

        知识点:
          - @transaction.atomic: 整个方法在事务中
          - 状态机检查: 只有 PENDING 才能支付
        """
        if self.status != OrderStatus.PENDING.value:
            raise ValueError(f"订单状态 {self.status} 不可支付")

        from django.utils import timezone
        self.status = OrderStatus.PROCESSING.value
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at", "updated_at"])

        # 创建支付记录
        PaymentLog.objects.create(
            order=self,
            amount=self.pay_amount,
            payment_method=payment_method,
        )

        return self

    @transaction.atomic
    def complete(self) -> "Order":
        """完成订单。"""
        if self.status != OrderStatus.PROCESSING.value:
            raise ValueError(f"订单状态 {self.status} 不可完成")
        self.status = OrderStatus.COMPLETED.value
        self.save(update_fields=["status", "updated_at"])
        return self

    @transaction.atomic
    def cancel(self, reason: str = "") -> "Order":
        """取消订单。"""
        if OrderStatus(self.status).is_terminal:
            raise ValueError("终态订单不可取消")
        self.status = OrderStatus.CANCELLED.value
        self.save(update_fields=["status", "updated_at"])
        return self


class OrderItem(BaseModel):
    """订单项。"""
    order = models.ForeignKey(
        Order, verbose_name="订单",
        on_delete=models.CASCADE, related_name="items",
    )
    product_name = models.CharField(verbose_name="商品名称", max_length=200)
    product_id = models.UUIDField(verbose_name="商品 ID")
    price = models.DecimalField(verbose_name="单价", max_digits=10, decimal_places=2)
    quantity = models.IntegerField(verbose_name="数量", default=1)
    subtotal = models.DecimalField(
        verbose_name="小计",
        max_digits=10, decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        db_table = "biz_order_item"
        verbose_name = "订单项"
        verbose_name_plural = "订单项列表"

    def save(self, *args, **kwargs) -> None:
        """自动计算小计。"""
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)


class PaymentLog(TimestampMixin):
    """支付记录。"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order, verbose_name="订单",
        on_delete=models.CASCADE, related_name="payment_logs",
    )
    amount = models.DecimalField(verbose_name="金额", max_digits=10, decimal_places=2)
    payment_method = models.CharField(verbose_name="支付方式", max_length=20)
    transaction_id = models.CharField(
        verbose_name="交易号", max_length=100, blank=True, default=""
    )
    status = models.CharField(
        verbose_name="状态",
        max_length=20,
        default="success",
    )

    class Meta:
        db_table = "biz_payment_log"
        verbose_name = "支付记录"
        verbose_name_plural = "支付记录"
        ordering = ["-created_at"]
