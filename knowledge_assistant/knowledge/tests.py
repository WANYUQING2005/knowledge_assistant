from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from account.models.user_models import User
from .models.knowledge_base_models import KnowledgeBase
from .models.document_models import Document
from .models.markdown_models import Markdown
from rest_framework.authtoken.models import Token
from account.models.profile_models import Profile
import uuid
import json



class KnowledgeAPITest(TestCase):

    def setUp(self):
        # 初始化DRF APIClient
        self.client = APIClient()
        # 创建测试用户
        # 使用create_user确保密码被正确哈希
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        # 创建关联的Profile，明确设置avatar为None而不是使用默认值
        self.profile = Profile.objects.create(
            user=self.user,
            avatar=None  # 明确设置为None
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
    def test_create_knowledge_base_case1(self):
      """测试创建知识库 - 用户1场景"""
      # 直接创建用户数据
      userid = str(self.user.id)
      kb_name = '测试知识库1'
      kb_desc = '用于测试的知识库1'

      url = reverse('create-knowledge-base')
    # 创建知识库
      data = {
        'name': kb_name,
        'description': kb_desc
      }
      response = self.client.post(url, data, format='json')
      print("Response data:", response.data)
    # 验证响应
      self.assertEqual(response.status_code, status.HTTP_201_CREATED)
      self.assertEqual(KnowledgeBase.objects.count(), 1)
      kb = KnowledgeBase.objects.get()
      self.assertEqual(kb.name, kb_name)
      self.assertEqual(kb.owner_user_id, userid)


    def test_upload_document_with_and_without_creater_id(self):
        """测试上传文档（带和不带creater_id）"""
        # 直接创建用户数据
        userid = str(self.user.id)
        kb_name = '测试知识库1'
        kb_desc = '用于测试的知识库1'

        # 创建知识库（只创建一次）
        url = reverse('create-knowledge-base')
        data = {
            'name': kb_name,
            'description': kb_desc
        }
        response = self.client.post(url, data, format='json')
        print("Response data1:", response.data)
        print()
        kb_id = response.data['id'] 

                # 测试场景1：不提供creater_id
        # 真实Markdown格式内容（约1000字符），包含标题层级、段落和列表结构
        file_content1 = """# 我的第一天

今天是我加入新公司的第一天，心情既兴奋又有些忐忑。早上6点半就醒了，比平时早了一个小时，可能是太期待了。洗漱完毕后，我特意挑了一件浅蓝色的衬衫，搭配卡其色裤子，希望能给同事们留下专业又亲和的印象。

## 早晨通勤

7点45分出门，选择了地铁通勤。早高峰的地铁果然名不虚传，人挤人，但幸运的是找到了一个座位。路上刷了一遍公司的官网，复习了一下核心业务和组织架构，生怕等会儿自我介绍时说错。

## 入职办理

8点50分到达公司前台，接待我的是行政部的张姐，她递给我一份入职登记表和员工手册，笑着说："欢迎加入，我们等你很久啦！"办理完手续后，她带我到了技术部的办公区。我的工位在团队角落，桌上已经放好了崭新的笔记本电脑和一个印有公司logo的马克杯，感觉很温馨。

## 团队介绍

部门经理李哥带我认识了团队成员：负责后端开发的老王是个资深程序员，说话幽默风趣；前端的小美刚入职半年，热情地分享了很多新人小贴士；测试组的强哥则给了我一份详细的测试流程文档。大家的友善让我紧张的心情放松了不少。

## 上午工作

10点开始熟悉工作环境，李哥给我分配了一个简单的任务：梳理用户注册模块的接口文档。刚开始有点摸不着头绪，老王主动过来帮我理清了思路，还推荐了几个实用的工具。中午12点，团队一起去公司楼下的餐厅吃饭，大家聊起了周末的计划，有人提议去爬山，有人想去看新上映的电影，氛围很融洽。

## 下午任务

下午2点开始着手处理接口文档，遇到不懂的地方就记在笔记本上，集中请教小李。她耐心地帮我讲解了每个字段的含义和设计逻辑，还分享了她之前整理的模板。到4点半时，我终于完成了文档初稿，李哥看了之后说："不错，第一次就能写成这样，继续加油！"得到认可的那一刻，心里特别有成就感。

## 下班时刻

6点准时下班，走出办公楼时，夕阳正染红了半边天。今天虽然有点累，但学到了很多东西，也感受到了团队的温暖。回家的路上，我给爸妈打了个电话，告诉他们第一天上班很顺利，妈妈在电话那头一直叮嘱我要好好吃饭，注意休息。

这真是充实又难忘的一天，期待明天的到来."""
        # 使用正确的Markdown文件扩展名和MIME类型
        file1 = SimpleUploadedFile(
            '我的一天.md',  # 修正为.md扩展名
            file_content1.encode('utf-8'),
            content_type='text/markdown'  # 标准Markdown MIME类型
        )
        upload_url = reverse('document-upload')
        data1 = {
            'knowledge_base_id': kb_id,
            'file': file1
        }
        response1 = self.client.post(upload_url, data1, format='multipart')
        print("Response data2 (without creater_id):", response1.data)
        print()

        # 验证场景1响应和数据库记录
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        doc1 = Document.objects.get(title='我的一天')
        self.assertEqual(doc1.creater_id, userid)

        # 测试场景2：提供creater_id='AAA'
        file_content2 = '1' * 1000
        file2 = SimpleUploadedFile(
            '我的两天.docx',
            file_content2.encode('utf-8'),
            content_type='markdown'
        )
        data2 = {
            'knowledge_base_id': kb_id,
            'file': file2,
            'creater_id': 'AAA'
        }
        response2 = self.client.post(upload_url, data2, format='multipart')
        print("Response data3 (with creater_id):", response2.data)
        print()

        # 验证场景2响应和数据库记录
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 2)
        doc2 = Document.objects.get(title='我的两天')
        self.assertEqual(doc2.creater_id, 'AAA')
        """测试上传用户id查看知识库列表"""
        self.kb2 = KnowledgeBase.objects.create(
            owner_user_id=str(self.user.id),
            name='测试知识库2',
            description='这是测试知识库2',
            embed_model='default'
        )
        url = reverse('knowledge-base-list')
        response = self.client.get(f'{url}?userid={self.user.id}')
        print("Response data4:", response.data)
        print()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        #self.assertEqual(response.data[0]['name'], '测试知识库1')
        #self.assertEqual(response.data[1]['name'], '测试知识库2')
        """测试上传知识库id查看文档列表"""
        kb_id=response.data[0]['id']
        # 提供有效kb_id，有文档
        url = reverse('document-list-by-kb')
        response = self.client.get(f'{url}?kb_id={kb_id}')
        print("Response data5:", response.data)
        print()
        # 验证返回字段
        expected_fields = ['id', 'title', 'file_type', 'creater_id', 'create_at']
        for doc in response.data:
            self.assertCountEqual(doc.keys(), expected_fields)
        # 验证文档ID
        """测试上传文档id查看内容"""
        returned_id=doc1.id
        url = reverse('document-detail')
        response = self.client.get(f'{url}?documentid={returned_id}')
        print("Response data6:", response.data)
        print()
        """测试上传文档id和number查看markdown"""
        # 修复：使用&分隔多个查询参数（原代码使用了?分隔number参数）
        url = reverse('markdown-by-document')
        response = self.client.get(f'{url}?documentid={returned_id}&number=2')  # 将?number=1改为&number=1
        print("Response data7:", response.data)
        print()
        """测试上传markdownid查看内容"""
        markdown_id=response.data['id']
        url = reverse('markdown-detail')
        response = self.client.get(f'{url}?markdownid={markdown_id}')
        print("Response data8:", response.data)
        print()
        """测试根据userid查看知识库列表"""
        url = reverse('knowledge-base-list')
        response = self.client.get(f'{url}?userid={self.user.id}')
        print("Response data9:", response.data)
        print()
        
        """测试根据documentid删除"""
        url = reverse('delete-document')
        # 修复：参数名从documentid改为document_id（与视图期望的参数名匹配）
        response = self.client.delete(f'{url}?document_id={returned_id}')
        print("Response data10:", response.data)
        print()
        """测试根据userid查看知识库列表"""
        url = reverse('knowledge-base-list')
        response = self.client.get(f'{url}?userid={self.user.id}')
        print("Response data11:", response.data)
        print()
        
        """测试根据knowledgebaseid删除"""
        url = reverse('delete-knowledge-base')
        # 修复：参数名从knowledgebaseid改为knowledge_base_id（与视图期望的参数名匹配）
        response = self.client.delete(f'{url}?knowledge_base_id={kb_id}')
        print("Response data12:", response.data)
        print()


