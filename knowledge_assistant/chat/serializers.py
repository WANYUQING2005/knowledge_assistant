from rest_framework import serializers
from .models.session_models import ChatSession

class ChatSessionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ChatSession
        fields = ['user_id', 'ai_type', 'kb_id']  # 移除title字段，它将由AI首次回答后生成
        extra_kwargs = {
            'kb_id': {'required': False, 'default': 0}
        }
    
    def validate(self, data):
        # 确保user_id不为空
        if not data.get('user_id'):
            raise serializers.ValidationError({
                'user_id': 'user_id为必填项'
            })
        
        # 确保ai_type有值（如果未提供，使用默认值1）
        if 'ai_type' not in data or data['ai_type'] is None:
            data['ai_type'] = 1
        
        # 确保kb_id有值（如果未提供，使用默认值0）
        if 'kb_id' not in data or data['kb_id'] is None:
            data['kb_id'] = 0
        
        return data