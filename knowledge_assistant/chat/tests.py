from .models import ChatSession, ChatMessage
from django.test import TestCase
from rest_framework.test import APIClient



class ChatAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = "test_user"
        self.kb_id = 0

    def test_chat_flow_and_db_save(self):
        """完整测试：创建会话 -> 发送消息 -> 检查数据库 -> 结束会话"""

        # 1. 创建会话
        create_url = "/chat/sessions/create/"
        response = self.client.post(create_url, {
            "user_id": self.user_id,
            "kb_id": self.kb_id,
            "ai_type": 1,
            "title": "测试会话",
            "is_active": True,
            "chat_count": 0
        }, format="json")
        print("创建会话返回:", response.status_code, response.data)
        if response.status_code != 201:
            return
        session_id = response.data["data"]["session_id"]

        # 确认会话写入数据库
        session = ChatSession.objects.get(id=session_id)
        print("数据库里的会话:", {
            "id": session.id,
            "user_id": session.user_id,
            "is_active": session.is_active,
            "chat_count": session.chat_count
        })

        # 2. 发送消息
        send_url = "/chat/messages/send/"
        question = "早上通勤"
        response = self.client.post(send_url, {
            "session_id": session_id,
            "sender":"user",
            "message":question,
            "user_id": self.user_id,
            "kb_id": self.kb_id,
            "content": question
        }, format="json")
        print("发送消息返回:", response.status_code, response.data)



        # 3. 检查数据库是否保存了消息
        user_msg = ChatMessage.objects.filter(session_id=session_id, sender="user").last()
        ai_msg = ChatMessage.objects.filter(session_id=session_id, sender="ai").last()
        print("数据库里最新的用户消息:", user_msg.content if user_msg else None)
        print("数据库里最新的AI消息:", ai_msg.content if ai_msg else None)
        print("AI消息metadata:", ai_msg.metadata if ai_msg else None)

        # 4. 结束会话
        end_url = "/chat/sessions/end/"
        response = self.client.post(end_url, {
            "session_id": session_id,
            "user_id": self.user_id,
        }, format="json")
        print("结束会话返回:", response.status_code, response.data)

        # 5. 确认会话在数据库中已标记为结束
        session.refresh_from_db()
        print("结束后数据库会话状态:", session.is_active)



