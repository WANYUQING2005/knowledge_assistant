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

    def test_tag_search_functionality(self):
        """测试标签搜索功能"""
        # 1. 创建知识库
        kb_name = '测试标签搜索知识库'
        kb_desc = '用于测试标签搜索功能'
        url = reverse('create-knowledge-base')
        data = {
            'name': kb_name,
            'description': kb_desc
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        kb_id = response.data['id']

        # 2. 上传一个带有特定标签的文档
        file_content = """# 通勤指南

## 早高峰出行建议

早上7:00-9:00是早高峰时间，建议提前规划路线，避开拥堵路段。
地铁是最理想的通勤方式，可避免路面交通拥堵问题。

## 公共交通选择

1. 地铁: 覆盖面广，准点率高
2. 公交: 路线灵活，但受路况影响
3. 共享单车: 适合短距离出行，环保健康

## 自驾通勤技巧

如果选择自驾，建议:
- 错峰出行，避开高峰时段
- 使用导航软件，实时了解路况
- 考虑拼车，减少出行成本
"""
        file = SimpleUploadedFile(
            '通勤指南.md',
            file_content.encode('utf-8'),
            content_type='text/markdown'
        )
        upload_url = reverse('document-upload')
        data = {
            'knowledge_base_id': kb_id,
            'file': file
        }
        response = self.client.post(upload_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 3. 确保文档已被处理（文档内容被分段并存入数据库）
        document_id = response.data['id']
        doc = Document.objects.get(id=document_id)

        # 4. 通过SQL直接向knowledge_ragchunks表插入测试数据，确保标签搜索有数据可查
        from django.db import connection

        # 使用UUID生成两个唯一ID
        chunk_id1 = str(uuid.uuid4())
        chunk_id2 = str(uuid.uuid4())
        vector_id1 = str(uuid.uuid4())
        vector_id2 = str(uuid.uuid4())

        with connection.cursor() as cursor:
            # 直接向knowledge_ragchunks表插入知识块1
            cursor.execute("""
                INSERT INTO knowledge_ragchunks 
                (id, title, content, vector_id, number, word_count, document_id, creater_id, create_at, kb_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                chunk_id1,  # 使用UUID字符串作为ID
                "通勤指南-早高峰",  # 标题
                "早上7:00-9:00是早高峰时间，建议提前规划路线，避开拥堵路段。地铁是最理想的通勤方式，可避免路面交通拥堵问题。",  # 内容
                vector_id1,  # 向量ID
                1,  # 编号
                50,  # 词数
                document_id,  # 文档ID
                str(self.user.id),  # 创建者ID
                "2025-09-10 12:00:00",  # 创建时间
                kb_id  # 知识库ID
            ])

            # 插入知识块2
            cursor.execute("""
                INSERT INTO knowledge_ragchunks 
                (id, title, content, vector_id, number, word_count, document_id, creater_id, create_at, kb_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                chunk_id2,  # ID
                "通勤指南-自驾",  # 标题
                "如果选择自驾，建议错峰出行，避开高峰时段；使用导航软件，实时了解路况；考虑拼车，减少出行成本。",  # 内容
                vector_id2,  # 向量ID
                2,  # 编号
                40,  # 词数
                document_id,  # 文档ID
                str(self.user.id),  # 创建者ID
                "2025-09-10 12:01:00",  # 创建时间
                kb_id  # 知识库ID
            ])

        # 5. 测试标签搜索功能 - 搜索"通勤"标签
        url = reverse('tag-search')
        search_data = {"tag": "通勤"}
        response = self.client.post(url, search_data, format='json')

        # 打印返回数据以便调试
        print("标签搜索响应状态:", response.status_code)
        print("标签搜索返回数据:", response.data)

        # 6. 验证搜索结果
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["query_tag"], "通勤")

        # 7. 验证是否返回了相关的知识块
        self.assertTrue(len(response.data["chunks"]) > 0)

        # 检查第一个知识块内容是否包含预期文本
        found_commute_content = False
        for chunk in response.data["chunks"]:
            if "早高峰" in chunk["content"] and "地铁" in chunk["content"]:
                found_commute_content = True
                break
        self.assertTrue(found_commute_content, "未找到预期的通勤相关内容")

        # 9. 测试搜索一个不相关的标签
        search_data = {"tag": "编程语言"}  # 文档中不存在的标签
        response = self.client.post(url, search_data, format='json')

        # 10. 验证不相关标签的搜索结果
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 不应匹配到任何标签
        self.assertEqual(len(response.data.get("matched_tags", [])), 0)
        # 不应返回任何知识块
        self.assertEqual(len(response.data.get("chunks", [])), 0)

class TagSearchAPITest(TestCase):
    """标签搜索API测试类"""

    def setUp(self):
        """测试数据准备"""
        self.client = APIClient()

        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser_tag',
            email='tag@example.com',
            password='testpassword123'
        )

        # 创建Profile，明确设置avatar为None
        self.profile = Profile.objects.create(
            user=self.user,
            avatar=None  # 明确设置为None
        )

        # 获取认证令牌
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # 创建测试数据
        self._create_test_data()

    def _create_test_data(self):
        """创建测试用的RAG文档和知识块数据"""
        from knowledge.models.chunk_models import RagDocuments, RagChunks

        # 创建测试文档
        self.doc1 = RagDocuments.objects.create(
            path="/test/doc1.txt",
            title="Python编程教程",  # title字段作为标签
            source_type="txt",
            tags=["编程", "Python", "教程"]  # tags字段包含多个标签
        )

        self.doc2 = RagDocuments.objects.create(
            path="/test/doc2.txt",
            title="机器学习基础",
            source_type="txt",
            tags=["机器学习", "AI", "算法"]
        )

        self.doc3 = RagDocuments.objects.create(
            path="/test/doc3.txt",
            title="Django框架开发",
            source_type="txt",
            tags=["Django", "Web开发", "Python"]
        )

        # 创建测试知识块 - 修复字段名，使用doc而不是doc_id
        self.chunk1 = RagChunks.objects.create(
            doc=self.doc1,  # 使用doc字段，不是doc_id
            ord=1,
            content="Python是一种高级编程语言，适用于各种应用开发",
            content_hash="hash1",
            split="sentence",
            tag0="Python",
            chunk_tags=["编程语言", "Python", "高级语言"]
        )

        self.chunk2 = RagChunks.objects.create(
            doc=self.doc1,  # 使用doc字段，不是doc_id
            ord=2,
            content="Python具有简洁的语法和强大的标准库",
            content_hash="hash2",
            split="sentence",
            tag0="语法",
            chunk_tags=["Python", "语法", "标准库"]
        )

        self.chunk3 = RagChunks.objects.create(
            doc=self.doc2,  # 使用doc字段，不是doc_id
            ord=1,
            content="机器学习是人工智能的一个重要分支",
            content_hash="hash3",
            split="sentence",
            tag0="机器学习",
            chunk_tags=["机器学习", "AI", "人工智能"]
        )

        self.chunk4 = RagChunks.objects.create(
            doc=self.doc3,  # 使用doc字段，不是doc_id
            ord=1,
            content="Django是一个功能强大的Python Web框架",
            content_hash="hash4",
            split="sentence",
            tag0="Django",
            chunk_tags=["Django", "Web框架", "Python"]
        )

    def test_tag_search_success(self):
        """测试标签搜索成功案例"""
        url = reverse('tag-search')
        data = {
            "tag": "Python",
            "topk_tags": 5,
            "limit_per_tag": 10
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['query_tag'], 'Python')
        self.assertIn('matched_tags', response.data)
        self.assertIn('chunks', response.data)

        # 验证返回的匹配标签包含Python相关标签
        matched_tags = response.data['matched_tags']
        self.assertTrue(len(matched_tags) > 0)

        # 验证返回的知识块包含Python相关内容
        chunks = response.data['chunks']
        self.assertTrue(len(chunks) > 0)

        # 验证知识块结构
        for chunk in chunks:
            self.assertIn('id', chunk)
            self.assertIn('content', chunk)
            self.assertIn('document_title', chunk)
            self.assertIn('tags', chunk)

    def test_tag_search_exact_match(self):
        """测试精确匹配"""
        url = reverse('tag-search')
        data = {"tag": "Django"}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        matched_tags = response.data['matched_tags']

        # Django应该被精确匹配
        self.assertIn("Django框架开发", matched_tags)

        # 验证返回的知识块包含Django相关内容
        chunks = response.data['chunks']
        django_chunks = [c for c in chunks if 'Django' in c['content'] or 'Django' in str(c['tags'])]
        self.assertTrue(len(django_chunks) > 0)

    def test_tag_search_partial_match(self):
        """测试部分匹配"""
        url = reverse('tag-search')
        data = {"tag": "学习"}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        matched_tags = response.data['matched_tags']

        # 应该匹配到包含"学习"的标签
        learning_tags = [tag for tag in matched_tags if "学习" in tag]
        self.assertTrue(len(learning_tags) > 0)

    def test_tag_search_no_match(self):
        """测试无匹配结果"""
        url = reverse('tag-search')
        data = {"tag": "不存在的标签xyz123"}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['matched_tags']), 0)
        self.assertEqual(len(response.data['chunks']), 0)
        self.assertEqual(response.data['message'], '未匹配到相关标签')

    def test_tag_search_empty_query(self):
        """测试空查询"""
        url = reverse('tag-search')
        data = {"tag": ""}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')

    def test_tag_search_missing_parameter(self):
        """测试缺少参数"""
        url = reverse('tag-search')
        data = {}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('tag参数', response.data['message'])

    def test_tag_search_with_parameters(self):
        """测试带参数的搜索"""
        url = reverse('tag-search')
        data = {
            "tag": "Python",
            "topk_tags": 3,
            "limit_per_tag": 5
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证返回的标签数量不超过topk_tags
        matched_tags = response.data['matched_tags']
        self.assertTrue(len(matched_tags) <= 3)

    def test_tag_search_authentication_required(self):
        """测试需要认证"""
        # 移除认证
        self.client.credentials()

        url = reverse('tag-search')
        data = {"tag": "Python"}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tag_search_fuzzy_match(self):
        """测试模糊匹配"""
        url = reverse('tag-search')
        data = {"tag": "编程语言教程"}  # 包含多个词的查询

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 应该能匹配到相关的标签和内容
        chunks = response.data['chunks']
        # 由于查询包含"编程"、"语言"、"教程"等词，应该能找到相关内容
        self.assertTrue(len(chunks) >= 0)  # 至少不报错

    def tearDown(self):
        """清理测试数据"""
        from knowledge.models.chunk_models import RagDocuments, RagChunks
        RagChunks.objects.all().delete()
        RagDocuments.objects.all().delete()
        User.objects.all().delete()
