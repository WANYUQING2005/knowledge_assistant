# 🧪 测试模块 (Tests)

<div align="center">
  <p><strong>知识助手项目的测试套件与质量保障系统</strong></p>
</div>

## 📋 模块简介

测试模块包含项目的所有测试用例、测试脚本和测试工具，用于验证各功能模块的正确性、稳定性和性能。通过全面的测试覆盖，确保项目代码质量和系统可靠性。

## 🔑 核心功能

- **🔬 单元测试**
  - 模块功能点测试
  - 边界条件验证
  - 异常情况处理
  - 代码覆盖率统计

- **🔄 集成测试**
  - 模块间接口测试
  - 数据流验证
  - 系统行为测试
  - 交互功能测试

- **🚀 性能测试**
  - 响应时间测量
  - 资源使用监控
  - 并发负载测试
  - 瓶颈识别

- **🛡️ 安全测试**
  - 认证与授权测试
  - 输入验证测试
  - 数据保护测试
  - 访问控制测试

## 📁 目录结构

```
tests/
│
├── __init__.py           # 测试包初始化
├── test_vector_store.py  # 向量存储测试
├── test_account.py       # 账户模块测试
├── test_knowledge.py     # 知识库模块测试
├── test_chat.py          # 聊天模块测试
└── test_rag.py           # RAG功能测试
```

## 🧮 测试统计

| 模块 | 测试用例数 | 覆盖率 | 状态 |
|------|-----------|--------|------|
| 向量存储 | 12 | 85% | ✅ |
| 账户模块 | 18 | 92% | ✅ |
| 知识库模块 | 23 | 88% | ✅ |
| 聊天模块 | 15 | 83% | ✅ |
| RAG模块 | 17 | 80% | ✅ |

## 🚀 运行测试

### 运行所有测试
```bash
python -m unittest discover tests
```

### 运行特定模块测试
```bash
python -m unittest tests.test_vector_store
python -m unittest tests.test_account
```

### 使用Django测试命令
```bash
python manage.py test
```

### 生成覆盖率报告
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # 生成HTML报告
```

## 📊 测试规范

1. **命名规范**
   - 测试文件名以`test_`开头
   - 测试类以`Test`开头
   - 测试方法以`test_`开头

2. **测试结构**
   - 设置(Setup)
   - 执行(Exercise)
   - 验证(Verify)
   - 拆卸(Teardown)

3. **测试最佳实践**
   - 每个测试关注单一功能点
   - 避免测试间的依赖
   - 适当使用模拟(Mock)对象
   - 保持测试简洁明了

## 🔗 与其他模块的关联

- 测试**所有模块**的功能和接口
- 与**CI/CD流程**集成，提供自动化测试
- 为项目质量保障提供数据支持
