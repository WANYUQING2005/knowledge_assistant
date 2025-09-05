from django.urls import path
from .views import CreateChatSessionView

urlpatterns = [
    # 创建ChatSession的API端点
    path('sessions/create/', CreateChatSessionView.as_view(), name='create_chat_session'),
]