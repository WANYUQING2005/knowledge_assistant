from AiChat import *
from tag_search import *
from kb import *


while True:
    print("选择你需要运行的程序：")
    print("1. 首次运行demo")
    print("2. 创建MySQL数据库表")
    print("3. 创建数据库内容和向量索引")
    print("4. 交互式问答")
    print("5. 基于标签的搜索")
    print("6. 退出")
    print("--------------------------")
    choice = input("请输入选项（1-6）：").strip()
    if choice == '1':
        init_mysql()
        create_mysql_faiss()
        aichat()
        tag_search()
    elif choice == '2':
        init_mysql()
    elif choice == '3':
        create_mysql_faiss()
    elif choice == '4':
        aichat()
    elif choice == '5':
        tag_search()
    elif choice == '6':
        print("程序已退出")
        break
    else:
        print("无效选项，请重新输入。")

    print("-----------------------------")


