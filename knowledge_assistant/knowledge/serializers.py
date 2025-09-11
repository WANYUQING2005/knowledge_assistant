from rest_framework import serializers
from .models.knowledge_base_models import KnowledgeBase
from .models.document_models import Document
from .models.markdown_models import Markdown
class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = ('id', 'name', 'description', 'embed_model','create_at','storage_size')
        read_only_fields = ('id', 'owner_user_id', 'create_at','storage_size')

    def validate_name(self, value):
        # 获取当前用户ID
        user_id = self.context['request'].user.id
        # 检查同名知识库
        if KnowledgeBase.objects.filter(owner_user_id=user_id, name=value).exists():
            raise serializers.ValidationError("您已存在同名知识库")
        return value
class DocumentSerializer(serializers.ModelSerializer):
    creater_id = serializers.CharField(required=False, allow_null=False)

    class Meta:
        model = Document
        fields = ['id', 'knowledge_base_id', 'title', 'file_type', 'creater_id', 'storage_uri', 'chunk_count', 'create_at']
        read_only_fields = ['id', 'storage_uri', 'chunk_count', 'create_at']

    def validate(self, data):
        # 获取knowledge_base_id
        knowledge_base_id = data.get('knowledge_base_id')
        # 如果未提供creater_id，则从知识库获取owner_user_id
        if not data.get('creater_id'):
            try:
                knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
                data['creater_id'] = knowledge_base.owner_user_id
            except KnowledgeBase.DoesNotExist:
                raise serializers.ValidationError("关联的知识库不存在")
        return data
class DocumentDetailSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['knowledge_base_id', 'title', 'file_type', 'chunk_count', 'create_at', 'content', 'creater_id']

    def get_content(self, obj):
        # 合并所有Markdown块内容作为完整文件正文
        markdowns = Markdown.objects.filter(document_id=obj.id).order_by('number')
        return '\n'.join([md.content for md in markdowns])
class MarkdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Markdown
        fields = ['title', 'content', 'number', 'word_count', 'document_id', 'creater_id', 'create_at','id','vector_id']
        read_only_fields = fields


class DocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'title', 'file_type', 'creater_id', 'create_at')