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
        # 打印AI回答内容
        if response.status_code == 200 and "answer" in response.data:
            print("\n问题: {}\n回答: {}\n".format(question, response.data["answer"]))


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

    def test_multi_turn_conversation(self):
        """多轮对话测试：创建会话 -> 发送多轮消息 -> 验证历史消息使用正确 -> 结束会话"""
        print("\n\n============= 开始多轮对话测试 =============\n")

        # 1. 创建会话
        create_url = "/chat/sessions/create/"
        response = self.client.post(create_url, {
            "user_id": self.user_id,
            "kb_id": self.kb_id,
            "ai_type": 1,
            "title": "多轮对话测试会话",
            "is_active": True,
            "chat_count": 0
        }, format="json")

        self.assertEqual(response.status_code, 201, "会话创建失败")
        session_id = response.data["data"]["session_id"]
        print(f"创建会话成功，会话ID: {session_id}")

        # 初始会话状态验证
        session = ChatSession.objects.get(id=session_id)
        self.assertEqual(session.chat_count, 0, "初始对话计数应为0")
        self.assertEqual(session.is_active, True, "初始会话状态应为活跃")

        # 进行多轮对话
        send_url = "/chat/messages/send/"

        # 第一轮对话
        first_question = "什么是向量数据库?"
        print(f"\n===== 第一轮对话 =====")
        print(f"用户问题: {first_question}")

        response_1 = self.client.post(send_url, {
            "session_id": session_id,
            "user_id": self.user_id,
            "kb_id": self.kb_id,
            "sender": "user",
            "content": first_question
        }, format="json")

        self.assertEqual(response_1.status_code, 200, "第一轮消息发送失败")
        self.assertTrue("answer" in response_1.data, "第一轮回答不完整")

        # 打印回答内容
        print(f"AI回答: {response_1.data['answer']}")
        if "sources" in response_1.data:
            print(f"参考来源: {response_1.data['sources']}")

        # 验证第一轮对话数据库存储
        session.refresh_from_db()
        self.assertEqual(session.chat_count, 1, "第一轮对话后计数应为1")

        # 第二轮对话 - 基于第一轮的上下文提问
        second_question = "它与传统数据库有什么区别?"
        print(f"\n===== 第二轮对话 =====")
        print(f"用户问题: {second_question}")

        response_2 = self.client.post(send_url, {
            "session_id": session_id,
            "user_id": self.user_id,
            "kb_id": self.kb_id,
            "sender": "user",
            "content": second_question
        }, format="json")

        self.assertEqual(response_2.status_code, 200, "第二轮消息发送失败")
        self.assertTrue("answer" in response_2.data, "第二轮回答不完整")

        # 打印回答内容
        print(f"AI回答: {response_2.data['answer']}")
        if "sources" in response_2.data:
            print(f"参考来源: {response_2.data['sources']}")

        # 验证第二轮对话数据库存储
        session.refresh_from_db()
        self.assertEqual(session.chat_count, 2, "第二轮对话后计数应为2")

        # 第三轮对话 - 继续基于前两轮对话提问
        third_question = "你能举例说明向量数据库的应用场景吗?"
        print(f"\n===== 第三轮对话 =====")
        print(f"用户问题: {third_question}")

        response_3 = self.client.post(send_url, {
            "session_id": session_id,
            "user_id": self.user_id,
            "kb_id": self.kb_id,
            "sender": "user",
            "content": third_question
        }, format="json")

        self.assertEqual(response_3.status_code, 200, "第三轮消息发送失败")
        self.assertTrue("answer" in response_3.data, "第三轮回答不完整")

        # 打印回答内容
        print(f"AI回答: {response_3.data['answer']}")
        if "sources" in response_3.data:
            print(f"参考来源: {response_3.data['sources']}")

        # 检查所有消息记录
        all_messages = ChatMessage.objects.filter(session_id=session_id).order_by('chat_number')
        self.assertEqual(len(all_messages), 6, "应该有6条消息记录(3轮问答)")

        # 获取按发送时间排序的用户消息和AI消息
        user_messages = list(ChatMessage.objects.filter(
            session_id=session_id, sender="user"
        ).order_by('chat_number'))

        ai_messages = list(ChatMessage.objects.filter(
            session_id=session_id, sender="ai"
        ).order_by('chat_number'))

        # 验证用户消息内容
        self.assertEqual(len(user_messages), 3, "应有3条用户消息")
        self.assertEqual(user_messages[0].content, first_question, "第一条用户消息内容不匹配")
        self.assertEqual(user_messages[1].content, second_question, "第二条用户消息内容不匹配")
        self.assertEqual(user_messages[2].content, third_question, "第三条用户消息内容不匹配")

        # 验证AI消息是否包含sources元数据
        self.assertEqual(len(ai_messages), 3, "应有3条AI消息")
        for i, msg in enumerate(ai_messages):
            self.assertTrue("sources" in msg.metadata, f"第{i+1}轮AI回复缺少sources元数据")

        # 打印所有对话历史总结
        print("\n===== 完整对话历史 =====")
        for idx, msg in enumerate(all_messages):
            role = "用户" if msg.sender == "user" else "AI"
            print(f"{role}: {msg.content[:100]}..." if len(msg.content) > 100 else f"{role}: {msg.content}")

        # 结束会话
        end_url = "/chat/sessions/end/"
        response = self.client.post(end_url, {
            "session_id": session_id,
            "user_id": self.user_id,
        }, format="json")

        self.assertEqual(response.status_code, 200, "结束会话失败")

        # 验证会话已结束
        session.refresh_from_db()
        self.assertEqual(session.is_active, False, "会话应该已标记为非活跃")

        # 验证结束会话响应中的统计信息
        self.assertEqual(response.data["data"]["message_count"], 6, "消息总数应为6")
        self.assertEqual(response.data["data"]["user_message_count"], 3, "用户消息数应为3")
        self.assertEqual(response.data["data"]["ai_message_count"], 3, "AI消息数应为3")

        print("\n============= 多轮对话测试结束 =============\n")
