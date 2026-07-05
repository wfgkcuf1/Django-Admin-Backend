"""
用户模块测试。

知识点:
  1. TestCase: Django 测试基类
  2. setUp: 测试前准备
  3. Client: 模拟 HTTP 请求
  4. APITestCase: DRF 测试基类
  5. assertEqual / assertTrue / assertIn: 断言
  6. 工厂数据准备
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    """用户模型测试。"""

    def setUp(self):
        """每个测试前执行。"""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
        )

    def test_user_creation(self):
        """测试用户创建。"""
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("testpass123"))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_superuser)

    def test_user_role_default(self):
        """测试默认角色。"""
        self.assertEqual(self.user.role, "user")

    def test_display_name(self):
        """测试显示名称。"""
        self.assertEqual(self.user.display_name, "testuser")
        self.user.nickname = "测试用户"
        self.assertEqual(self.user.display_name, "测试用户")

    def test_str_representation(self):
        """测试 __str__。"""
        self.assertEqual(str(self.user), "testuser")


class UserAPITest(APITestCase):
    """用户 API 测试。"""

    def setUp(self):
        self.register_url = "/api/v1/auth/register/"
        self.login_url = "/api/v1/auth/login/"
        self.user_data = {
            "username": "apitest",
            "password": "TestPass123",
            "confirm_password": "TestPass123",
            "email": "apitest@example.com",
        }

    def test_register(self):
        """测试注册。"""
        response = self.client.post(
            self.register_url,
            self.user_data,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data.get("data", {}))

    def test_login(self):
        """测试登录。"""
        # 先注册
        self.client.post(self.register_url, self.user_data, format="json")
        # 再登录
        response = self.client.post(
            self.login_url,
            {"username": "apitest", "password": "TestPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data.get("data", {}))

    def test_login_wrong_password(self):
        """测试错误密码登录。"""
        response = self.client.post(
            self.login_url,
            {"username": "nobody", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
