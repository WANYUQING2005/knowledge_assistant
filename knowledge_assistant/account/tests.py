from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models.user_models import User
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models.profile_models import Profile
from rest_framework.authtoken.models import Token

class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')  # 确保与urls.py中注册端点的name一致
        self.valid_data = {
            'userid': str(self.user.id),
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'TestPassword123!'
        }

    def test_successful_registration(self):
        # 确保注册接口不需要认证
        self.client.force_authenticate(user=None)
        # 发送注册请求
        response = self.client.post(self.register_url, self.valid_data, format='json')

        # 验证响应状态码和内容
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        # 删除对username的断言，因为响应中不再返回该字段
        
        # 验证数据库中是否存在关联的Profile
        self.assertTrue(Profile.objects.filter(user__email=self.valid_data['email']).exists())

    def test_duplicate_username(self):
        # 先创建一个用户
        User.objects.create_user(
            email='existing@example.com',
            username=self.valid_data['username'],
            password='ExistingPassword123!'
        )

        # 尝试使用相同用户名注册
        response = self.client.post(self.register_url, self.valid_data, format='json')

        # 验证返回错误状态码
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['message'])

    def test_invalid_email_format(self):
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email'

        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['message'])

    def test_short_password(self):
        invalid_data = self.valid_data.copy()
        invalid_data['password'] = 'short'

        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['message'])
User = get_user_model()

class AccountViewsTestCase(APITestCase):
    def setUp(self):
        # 创建测试用户
        # 使用create_user确保密码被正确哈希
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        # 创建关联的Profile
        self.profile = Profile.objects.create(
            user=self.user,
            avatar=None
        )
        # 获取认证令牌
        self.token = Token.objects.create(user=self.user)
        # 显式设置Authorization头
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        # 添加令牌验证调试
        print(f"Token being used: {self.token.key}")
        response = self.client.get(reverse('user-detail'))
        print(f"Authentication response status: {response.status_code}")
        print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, "初始认证失败，请检查令牌生成逻辑")


    def test_user_update_view_success(self):
        """测试成功更新用户信息"""
        url = reverse('user-update')
        data = {
            'userid': str(self.user.id),
            'username': 'updatedname',
            'bio': 'Updated bio information'
        }
        response = self.client.post(url, data, format='json')
        print("Response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        # 验证数据库数据已更新
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updatedname')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Updated bio information')

   

    def test_password_update_view_success(self):
        url = reverse('password-update')
        
        # 调试：验证用户当前密码
        is_old_password_correct = self.user.check_password('testpassword123')
        print(f"用户当前密码是否为'testpassword123': {is_old_password_correct}")
        print(f"用户ID: {self.user.id}, 测试数据用户ID: {str(self.user.id)}")
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        data = {
            'userid': str(self.user.id),
            'old_password': 'testpassword123',
            'new_password': 'Newpassword123@',
            'confirm_password': 'Newpassword123@'
        } 
        # 添加调试：打印请求头和数据

        print(f"发送的数据: {data}")
        # 调试：打印发送的请求数据
        print(f"发送的请求数据: {data}")
        response = self.client.post(url, data, format='json')
        print("Response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 添加调试输出
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_update_invalid_old_password(self):
        """测试旧密码错误时更新失败"""
        url = reverse('password-update')
        data = {
            'user_id': str(self.user.id),
            'old_password': 'wrongpassword',
            'new_password': 'newpassword456'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data['errors'])

    def test_user_detail_view(self):
        """测试获取用户详情"""
        url = reverse('user-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['id'], self.user.id)
        
    def test_user_delete_view_success(self):
        url = reverse('user-delete')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {'user_id': self.user.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证用户已删除
        self.assertFalse(User.objects.filter(id=self.user.id).exists())