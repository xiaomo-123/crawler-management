# 问答爬虫API文档

## API列表

### 1. 初始化问答爬虫缓存

**接口描述**: 初始化问答爬虫缓存，会先清空现有缓存，然后从raw_data表加载所有answer_url到Redis

**请求方式**: POST

**请求路径**: `/api/qa-crawler/init`

**请求参数**: 无

**响应示例**:
```json
{
  "success": true,
  "message": "成功加载 100 个URL到缓存",
  "count": 100
}
```

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/qa-crawler/init"   -H "Content-Type: application/json"
```

---

### 2. 检查缓存是否存在

**接口描述**: 检查问答爬虫URL缓存是否存在，并返回缓存的URL数量

**请求方式**: GET

**请求路径**: `/api/qa-crawler/check`

**请求参数**: 无

**响应示例**:
```json
{
  "exists": true,
  "count": 100
}
```

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/qa-crawler/check"   -H "Content-Type: application/json"
```

---

### 3. 提交问答爬虫数据

**接口描述**: 提交问答爬虫数据，自动处理URL缓存和队列管理

**请求方式**: POST

**请求路径**: `/api/qa-crawler/submit`

**请求参数**:
```json
{
  "rank": 1,
  "title": "有没有校园救赎文小说推荐？",
  "url": "https://www.zhihu.com/question/477700106/answer/2751118654",
  "question_detail": "",
  "answer_content_text": "神想让我攻略我那阴沉厌世的同桌。\n\n我并不想接受这个任务，也不认为自己可以。\n\n救赎，这两个字很重。\n\n救他人，赎上自己。",
  "content": "神想让我攻略我那阴沉厌世的同桌。\n\n我并不想接受这个任务，也不认为自己可以。\n\n救赎，这两个字很重。\n\n救他人，赎上自己。",
  "author": "子衣",
  "author_url": "https://www.zhihu.com/people/zi-yi-16-90-47",
  "author_field": "文学",
  "author_cert": "优秀回答者",
  "author_fans": 1250,
  "year": 2023,
  "publish_time": "2023-11-09",
  "images": [
    "https://pic1.zhimg.com/50/v2-6828220b1fd53511650568b98702a5bc_720w.jpg?source=2c26e567"
  ],
  "comments_structured": [
    {
      "author": "子衣",
      "author_url": "https://www.zhihu.com/people/zi-yi-16-90-47",
      "content": "呜呜呜，真的好好看！爱自己爱别人的故事[可怜][可怜][可怜]",
      "like_count": 1784,
      "time": "2022-11-09 04:59:21"
    },
    {
      "author": "L-蓝恬",
      "author_url": "https://www.zhihu.com/people/l-lan-tian",
      "content": "完结 强推",
      "like_count": 692,
      "time": "2022-11-13 15:17:45"
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "数据已提交",
  "url_exists": false
}
```

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/qa-crawler/submit"   -H "Content-Type: application/json"   -d '{
    "rank": 1,
    "title": "有没有校园救赎文小说推荐？",
    "url": "https://www.zhihu.com/question/477700106/answer/2751118654",
    "question_detail": "",
    "answer_content_text": "神想让我攻略我那阴沉厌世的同桌。\n\n我并不想接受这个任务，也不认为自己可以。\n\n救赎，这两个字很重。\n\n救他人，赎上自己。",
    "content": "神想让我攻略我那阴沉厌世的同桌。\n\n我并不想接受这个任务，也不认为自己可以。\n\n救赎，这两个字很重。\n\n救他人，赎上自己。",
    "author": "子衣",
    "author_url": "https://www.zhihu.com/people/zi-yi-16-90-47",
    "author_field": "文学",
    "author_cert": "优秀回答者",
    "author_fans": 1250,
    "year": 2023,
    "publish_time": "2023-11-09",
    "images": [
      "https://pic1.zhimg.com/50/v2-6828220b1fd53511650568b98702a5bc_720w.jpg?source=2c26e567"
    ],
    "comments_structured": [
      {
        "author": "子衣",
        "author_url": "https://www.zhihu.com/people/zi-yi-16-90-47",
        "content": "呜呜呜，真的好好看！爱自己爱别人的故事[可怜][可怜][可怜]",
        "like_count": 1784,
        "time": "2022-11-09 04:59:21"
      },
      {
        "author": "L-蓝恬",
        "author_url": "https://www.zhihu.com/people/l-lan-tian",
        "content": "完结 强推",
        "like_count": 692,
        "time": "2022-11-13 15:17:45"
      }
    ]
  }'
```

---

### 4. 获取队列状态

**接口描述**: 获取生产队列的状态信息

**请求方式**: GET

**请求路径**: `/api/qa-crawler/queue/status`

**请求参数**: 无

**响应示例**:
```json
{
  "queue_size": 10,
  "url_count": 100
}
```

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/qa-crawler/queue/status"   -H "Content-Type: application/json"
```

---

### 5. 处理队列中的数据

**接口描述**: 处理生产队列中的数据，批量保存到数据库（raw_data和comment_data子表）

**请求方式**: POST

**请求路径**: `/api/qa-crawler/queue/process`

**请求参数**:
- `batch_size` (可选): 每批处理的数据量，默认10，最大100

**响应示例**:
```json
{
  "processed": 10,
  "failed": 0
}
```

**curl示例**:
```bash
# 使用默认批次大小（10）
curl -X POST "http://localhost:8000/api/qa-crawler/queue/process"   -H "Content-Type: application/json"

# 指定批次大小为20
curl -X POST "http://localhost:8000/api/qa-crawler/queue/process?batch_size=20"   -H "Content-Type: application/json"
```

---

### 6. 清空问答爬虫缓存

**接口描述**: 清空问答爬虫的Redis缓存

**请求方式**: DELETE

**请求路径**: `/api/qa-crawler/clear`

**请求参数**: 无

**响应示例**:
```json
{
  "success": true,
  "message": "缓存已清空"
}
```

**curl示例**:
```bash
curl -X DELETE "http://localhost:8000/api/qa-crawler/clear"   -H "Content-Type: application/json"
```

---

## 使用流程

### 1. 初始化系统

首次使用时，初始化问答爬虫缓存：
```bash
curl -X POST "http://localhost:8000/api/qa-crawler/init"
```

### 2. 检查缓存状态

确认缓存是否正常：
```bash
curl -X GET "http://localhost:8000/api/qa-crawler/check"
```

### 3. 提交爬虫数据

爬虫程序获取数据后，通过API提交：
```bash
curl -X POST "http://localhost:8000/api/qa-crawler/submit"   -H "Content-Type: application/json"   -d '{
    "rank": 1,
    "title": "有没有校园救赎文小说推荐？",
    "url": "https://www.zhihu.com/question/477700106/answer/2751118654",
    "answer_content_text": "神想让我攻略我那阴沉厌世的同桌。\n\n我并不想接受这个任务，也不认为自己可以。\n\n救赎，这两个字很重。\n\n救他人，赎上自己。",
    "content": "神想让我攻略我那阴沉厌世的同桌。\n\n我并不想接受这个任务，也不认为自己可以。\n\n救赎，这两个字很重。\n\n救他人，赎上自己。",
    "author": "子衣",
    "author_url": "https://www.zhihu.com/people/zi-yi-16-90-47",
    "author_field": "文学",
    "author_cert": "优秀回答者",
    "author_fans": 1250,
    "year": 2023,
    "publish_time": "2023-11-09",
    "comments_structured": [
      {
        "author": "子衣",
        "author_url": "https://www.zhihu.com/people/zi-yi-16-90-47",
        "content": "呜呜呜，真的好好看！爱自己爱别人的故事[可怜][可怜][可怜]",
        "like_count": 1784,
        "time": "2022-11-09 04:59:21"
      }
    ]
  }'
```

### 4. 查看队列状态

检查队列中待处理的数据量：
```bash
curl -X GET "http://localhost:8000/api/qa-crawler/queue/status"
```

### 5. 处理队列数据

将队列中的数据批量保存到数据库：
```bash
curl -X POST "http://localhost:8000/api/qa-crawler/queue/process?batch_size=10"
```

### 6. 清空缓存

如需重新初始化，可先清空缓存：
```bash
curl -X DELETE "http://localhost:8000/api/qa-crawler/clear"
```

---

## 数据流程说明

1. **URL缓存管理**:
   - 系统维护两个URL缓存：问答爬虫URL缓存和推荐页URL缓存
   - 提交数据时，如果URL不存在，会同时添加到两个缓存中
   - 避免重复处理相同的URL

2. **数据队列**:
   - 提交的数据会被添加到生产队列
   - 队列中的数据按先进先出（FIFO）顺序处理
   - 支持批量处理，提高效率

3. **数据库存储**:
   - 主数据存储在raw_data表
   - 评论数据根据年月动态分配到对应的comment_data子表
   - 支持事务处理，确保数据一致性

4. **自动去重**:
   - 通过URL缓存实现自动去重
   - 已存在的URL不会被重复处理
   - 减少不必要的数据库操作
