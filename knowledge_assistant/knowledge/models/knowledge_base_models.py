from django.db import models
import uuid

def generate_knowledge_id():
    return str(uuid.uuid4())

class KnowledgeBase(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_knowledge_id, editable=False)
    owner_user_id = models.CharField(max_length=36)
    name = models.CharField(max_length=100, default="我的知识库")
    description = models.TextField(default="")
    embed_model = models.CharField(max_length=80, default="0")
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name