from django.db import models
import uuid

class ChatSession(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=36)
    title = models.CharField(max_length=200, default="新对话")
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    # 用户要求：增加chat_count表示对话总条数
    chat_count = models.IntegerField(default=0)
    # 用户要求：增加ai_type表示AI类型，默认为1
    ai_type = models.IntegerField(default=1)
    # 用户要求：增加kb_id表示该对话属于哪个知识库，不属于知识库时设为0
    kb_id = models.IntegerField(default=0)

    def __str__(self):
        return self.title