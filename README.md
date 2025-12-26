# 小鲸鱼任务&API任务SQLite管理系统

基于 FastAPI 实现的小鲸鱼管理系统，包含账号管理、任务管理、代理管理、抽样导出等功能。

## 项目结构

```
crawler-management/
├── app/                    # 主应用代码
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用入口
│   ├── config.py          # 配置文件
│   ├── database.py        # 数据库连接
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── account.py     # 账号模型
│   │   ├── task.py        # 任务模型
│   │   ├── proxy.py       # 代理模型
│   │   ├── year_quota.py  # 年份配额模型
│   │   ├── raw_data.py    # 原始数据模型
│   │   └── sample_data.py # 抽样数据模型
│   ├── api/               # API 路由
│   │   ├── __init__.py
│   │   ├── accounts.py    # 账号管理API
│   │   ├── tasks.py       # 任务管理API
│   │   ├── proxies.py     # 代理管理API
│   │   ├── quotas.py      # 配额管理API
│   │   ├── raw_data.py    # 原始数据API
│   │   └── sample_data.py # 抽样数据API
│   ├── services/          # 业务逻辑
│   │   ├── __init__.py
│   │   ├── crawler.py     # 小鲸鱼服务
│   │   ├── sampler.py     # 抽样服务
│   │   └── exporter.py    # 导出服务
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── redis.py       # Redis 连接
│       └── helpers.py     # 辅助函数
├── static/                # 静态文件
│   ├── css/
│   │   └── style.css      # 样式文件
│   ├── js/
│   │   ├── app.js         # 主应用JS
│   │   ├── accounts.js    # 账号管理JS
│   │   ├── tasks.js       # 任务管理JS
│   │   ├── proxies.js     # 代理管理JS
│   │   └── dashboard.js   # 仪表盘JS
│   └── images/            # 图片资源
├── templates/             # HTML模板
│   ├── base.html          # 基础模板
│   ├── dashboard.html     # 仪表盘
│   ├── accounts.html      # 账号管理页面
│   ├── tasks.html         # 任务管理页面
│   └── proxies.html       # 代理管理页面
├── requirements.txt       # 依赖包
└── run.py                 # 启动脚本
```

## 功能特性

1. 账号管理：增删改查账号信息，管理账号状态
2. 任务管理：创建、执行、暂停、恢复、终止小鲸鱼任务
3. 代理管理：配置代理信息，支持多种代理策略
4. 抽样导出：按年份配额抽样数据并导出Excel
5. 数据展示：美观简洁的Web界面，实时展示任务状态和数据统计

## API 文档

启动服务后，访问 http://localhost:8000/docs 查看完整的API文档。

## 启动方法

1. 安装依赖：`pip install -r requirements.txt`
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
2. 启动服务：`python run.py`
3. 访问界面：http://localhost:8000

账号管理
# 创建账号
curl -X POST "http://localhost:8000/api/accounts/" \
-H "Content-Type: application/json" \
-d '{"account_name": "cookie内容", "status": 1}'

# 获取账号列表
curl -X GET "http://localhost:8000/api/accounts/"

# 更新账号
curl -X PUT "http://localhost:8000/api/accounts/1" \
-H "Content-Type: application/json" \
-d '{"status": 0}'

任务管理
# 创建任务
curl -X POST "http://localhost:8000/api/tasks/" \
-H "Content-Type: application/json" \
-d '{"task_name": "知乎小鲸鱼任务", "account_name": "cookie内容", "task_type": "crawler"}'

# 启动任务
curl -X POST "http://localhost:8000/api/tasks/1/start"

# 暂停任务
curl -X POST "http://localhost:8000/api/tasks/1/pause"

代理管理
# 创建代理
curl -X POST "http://localhost:8000/api/proxies/" \
-H "Content-Type: application/json" \
-d '{"proxy_type": "HTTP", "proxy_addr": "127.0.0.1:8080", "status": 1, "strategy": "轮询"}'

# 获取随机可用代理
curl -X GET "http://localhost:8000/api/proxies/random/available"
# 创建代理
curl -X POST "http://localhost:8000/api/proxies/" \
-H "Content-Type: application/json" \
-d '{"proxy_type": "HTTP", "proxy_addr": "127.0.0.1:8080", "status": 1, "strategy": "轮询"}'

# 获取随机可用代理
curl -X GET "http://localhost:8000/api/proxies/random/available"



配额管理
# 初始化配额
curl -X POST "http://localhost:8000/api/quotas/init"

# 创建配额
curl -X POST "http://localhost:8000/api/quotas/" \
-H "Content-Type: application/json" \
-d '{"year": 2023, "stock_ratio": 0.8, "sample_num": 8000}'

原始数据管理
# 创建原始数据
curl -X POST "http://localhost:8000/api/raw-data/" \
-H "Content-Type: application/json" \
-d '{
  "title": "如何学习Python",
  "content": "Python是一门非常流行的编程语言...",
  "publish_time": "2023-05-15 10:30:00",
  "answer_url": "https://www.zhihu.com/question/123456/answer/789012",
  "author": "Python专家",
  "author_url": "https://www.zhihu.com/people/python-expert",
  "author_field": "计算机科学",
  "author_cert": "优秀回答者",
  "author_fans": 5000,
  "year": 2023,
  "task_id": 1
}'

# 获取原始数据列表
curl -X GET "http://localhost:8000/api/raw-data/"

# 按年份过滤获取原始数据
curl -X GET "http://localhost:8000/api/raw-data/?year=2023"

# 按任务ID过滤获取原始数据
curl -X GET "http://localhost:8000/api/raw-data/?task_id=1"

# 获取单个原始数据
curl -X GET "http://localhost:8000/api/raw-data/1"

# 更新原始数据
curl -X PUT "http://localhost:8000/api/raw-data/1" \
-H "Content-Type: application/json" \
-d '{
  "title": "更新后的标题",
  "content": "更新后的内容..."
}'

# 删除原始数据
curl -X DELETE "http://localhost:8000/api/raw-data/1"

# 获取按年份统计的原始数据
curl -X GET "http://localhost:8000/api/raw-data/stats/by-year"

# 获取按任务统计的原始数据
curl -X GET "http://localhost:8000/api/raw-data/stats/by-task"

抽样数据
# 按配额抽样数据
curl -X POST "http://localhost:8000/api/sample-data/sample"

# 获取按年份统计的抽样数据
curl -X GET "http://localhost:8000/api/sample-data/stats/by-year"
