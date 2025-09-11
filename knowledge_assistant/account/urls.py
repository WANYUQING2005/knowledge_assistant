from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('update/', views.UserUpdateView.as_view(), name='user-update'),
    path('delete/', views.UserDeleteView.as_view(), name='user-delete'),
    path('password/update/', views.PasswordUpdateView.as_view(), name='password-update'),
    path('detail/', views.UserDetailView.as_view(), name='user-detail'),

    # 其他用户相关路由
]