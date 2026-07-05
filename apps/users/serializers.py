"""
用户序列化器 — 登录、注册、用户 CRUD。

知识点:
  1. `Serializer` vs `ModelSerializer`
  2. `write_only`: 只在写入时包含（如密码）
  3. `read_only`: 只读字段（如 created_at）
  4. 嵌套序列化器
  5. 自定义验证逻辑
  6. `validate_<field>` 字段级验证
  7. `validate` 对象级验证
"""
import re
from typing import Any, Optional

from django.contrib.auth import authenticate
from rest_framework import serializers

from common.base_serializer import BaseModelSerializer
from common.enums import UserRole, Gender
from common.utils import mask_phone, mask_email
from .models import User


class UserListSerializer(BaseModelSerializer):
    """
    用户列表序列化器 — 只输出摘要信息。

    知识点:
      - SerializerMethodField: 自定义序列化字段
      - 数据脱敏
      - 枚举标签转换
    """

    role_label = serializers.SerializerMethodField()
    gender_label = serializers.SerializerMethodField()
    phone_masked = serializers.SerializerMethodField()
    email_masked = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "nickname", "phone", "phone_masked",
            "email", "email_masked", "role", "role_label",
            "gender", "gender_label", "avatar", "is_active",
            "is_staff", "is_superuser", "last_login",
            "last_active_at", "date_joined", "created_at", "updated_at",
        ]
        read_only_fields = [
            "last_login", "last_active_at", "date_joined",
            "created_at", "updated_at",
        ]

    def get_role_label(self, obj: User) -> str:
        """角色中文名。"""
        return obj.role_label

    def get_gender_label(self, obj: User) -> str:
        """性别中文名。"""
        try:
            return Gender(obj.gender).name
        except ValueError:
            return "未知"

    def get_phone_masked(self, obj: User) -> str:
        """脱敏手机号。"""
        return mask_phone(obj.phone) if obj.phone else ""

    def get_email_masked(self, obj: User) -> str:
        """脱敏邮箱。"""
        return mask_email(obj.email) if obj.email else ""


class UserDetailSerializer(UserListSerializer):
    """
    用户详情序列化器 — 更多字段。

    知识点:
      - 继承列表序列化器并扩展
      - 嵌套序列化器显示关联数据
    """

    # 知识点: SerializerMethodField 隐藏敏感字段
    created_by_name = serializers.SerializerMethodField()

    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + [
            "created_by", "created_by_name",
        ]

    def get_created_by_name(self, obj: User) -> str:
        if obj.created_by:
            return obj.created_by.display_name
        return ""


class UserCreateSerializer(BaseModelSerializer):
    """
    用户创建序列化器。

    知识点:
      - password: write_only（不返回给客户端）
      - validate_phone: 字段级自定义验证
      - 重写 create: 调用 set_password
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        max_length=128,
        help_text="密码（6-128 位）",
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="确认密码",
    )

    class Meta:
        model = User
        fields = [
            "username", "password", "confirm_password",
            "email", "phone", "nickname", "role", "gender",
            "avatar", "is_active",
        ]

    def validate_phone(self, value: str) -> str:
        """手机号格式验证。"""
        if value and not re.match(r"^1[3-9]\d{9}$", value):
            raise serializers.ValidationError("手机号格式不正确")
        return value

    def validate_username(self, value: str) -> str:
        """用户名验证。"""
        if not re.match(r"^[a-zA-Z0-9_]{4,30}$", value):
            raise serializers.ValidationError(
                "用户名只能包含字母、数字、下划线，长度 4-30"
            )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        对象级验证 — 检查两次密码一致。

        知识点:
          - validate 方法: 跨字段验证
          - pop confirm_password: 不传到 model
        """
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError("两次密码不一致")
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """创建用户 — 调用 set_password 哈希密码。"""
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(BaseModelSerializer):
    """
    用户更新序列化器 — 不允许改密码（需要用单独接口）。

    知识点:
      - 部分字段 editable=False
      - 不需要密码字段
    """

    class Meta:
        model = User
        fields = [
            "email", "phone", "nickname", "gender",
            "avatar", "is_active", "role",
        ]
        # 知识点: extra_kwargs 用于为字段添加额外参数
        extra_kwargs = {
            "email": {"required": False},
            "phone": {"required": False},
        }


class UserPasswordSerializer(serializers.Serializer):
    """
    修改密码序列化器。

    知识点:
      - Serializer（非 ModelSerializer）: 手动定义字段
      - 自定义验证逻辑
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, min_length=6, max_length=128
    )
    confirm_password = serializers.CharField(
        required=True, min_length=6, max_length=128
    )

    def validate_old_password(self, value: str) -> str:
        """
        知识点:
          - validate_<field> 可以通过 self.context 访问 view 和 request
        """
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码不正确")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("两次新密码不一致")
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError("新密码不能与原密码相同")
        return attrs


# ─── JWT 相关序列化器 ───────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    """
    登录序列化器。

    知识点:
      - authenticate(): Django 的认证函数
      - 验证成功后返回 User 对象
      - 失败抛验证异常
    """

    username = serializers.CharField(required=True, help_text="用户名")
    password = serializers.CharField(
        write_only=True, required=True, help_text="密码"
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """验证用户名密码。"""
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("用户名或密码错误")
        if not user.is_active:
            raise serializers.ValidationError("该用户已被禁用")
        if user.deleted_at:
            raise serializers.ValidationError("该用户已被删除")

        attrs["user"] = user
        return attrs


class CustomTokenObtainSerializer(serializers.Serializer):
    """
    自定义 Token 获取序列化器 — 替换 simplejwt 默认的。

    simplejwt 默认返回 access + refresh，我们可以扩展更多字段。
    """
    pass  # simplejwt 会自动处理


class TokenResponseSerializer(serializers.Serializer):
    """
    Token 响应序列化器 — 定义登录成功返回的格式。

    知识点:
      - 用于 drf-spectacular API 文档生成
      - 不实际用于序列化/反序列化
    """

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserListSerializer()


class RegisterSerializer(UserCreateSerializer):
    """
    注册序列化器（复用创建逻辑）。

    知识点:
      - 继承已有的序列化器复用验证逻辑
      - 注册时强制 role=user
    """

    class Meta(UserCreateSerializer.Meta):
        # 注册不需要 role 字段
        fields = [
            "username", "password", "confirm_password",
            "email", "phone", "nickname",
        ]

    def validate_username(self, value: str) -> str:
        value = super().validate_username(value)
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def validate_email(self, value: str) -> str:
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("邮箱已被注册")
        return value

    def validate_phone(self, value: str) -> str:
        value = super().validate_phone(value)
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("手机号已被注册")
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        # 注册默认为普通用户
        validated_data["role"] = UserRole.USER.value
        return super().create(validated_data)
