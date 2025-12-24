# 创建原始数据 API 示例

## 请求方法
POST /api/raw-data/

## 请求头
Content-Type: application/json

## 请求体示例

```json
{
  "title": "如何提高编程能力？",
  "content": "<p>编程能力的提高需要多方面的努力，包括理论学习、实践练习和代码复盘...</p>",
  "publish_time": "2023-06-15",
  "answer_url": "https://example.com/answer/123456",
  "author": "技术达人",
  "author_url": "https://example.com/user/tech_master",
  "author_field": "计算机科学",
  "author_cert": "认证专家",
  "author_fans": 5000,
  "year": 2023,
  "task_id": 1,
  "comments_structured": [
    {
      "author": "Arlene Ran",
      "author_url": "https://www.zhihu.com/people/arlene-ran",
      "content": "给你免费做了个心肺复苏，还不赶紧谢谢人家[酷]",
      "like_count": 87,
      "time": "2023-06-16 14:29:20"
    },
    {
      "author": "倾译",
      "author_url": "https://www.zhihu.com/people/liu-ba-75",
      "content": "<p>我的天，都砸吐了啊，这威力真大</p>",
      "like_count": 37,
      "time": "2023-06-17 00:57:37"
    },
    {
      "author": "程序员小王",
      "author_url": "https://www.zhihu.com/people/programmer_wang",
      "content": "实践是提高编程能力的关键，多写代码，多思考，多总结。",
      "like_count": 125,
      "time": "2023-06-17 08:15:42"
    }
  ]
}
```

## cURL 命令示例

```bash
curl -X POST "http://localhost:8000/api/raw-data/" -H "Content-Type: application/json" -d '{
  "title": "如何提高编程能力？",
  "content": "<p>编程能力的提高需要多方面的努力，包括理论学习、实践练习和代码复盘...</p>",
  "publish_time": "2023-06-15",
  "answer_url": "https://example.com/answer/123456",
  "author": "技术达人",
  "author_url": "https://example.com/user/tech_master",
  "author_field": "计算机科学",
  "author_cert": "认证专家",
  "author_fans": 5000,
  "year": 2023,
  "task_id": 1,
  "comments_structured": [
    {
      "author": "Arlene Ran",
      "author_url": "https://www.zhihu.com/people/arlene-ran",
      "content": "给你免费做了个心肺复苏，还不赶紧谢谢人家[酷]",
      "like_count": 87,
      "time": "2023-06-16 14:29:20"
    },
    {
      "author": "倾译",
      "author_url": "https://www.zhihu.com/people/liu-ba-75",
      "content": "<p>我的天，都砸吐了啊，这威力真大</p>",
      "like_count": 37,
      "time": "2023-06-17 00:57:37"
    },
    {
      "author": "程序员小王",
      "author_url": "https://www.zhihu.com/people/programmer_wang",
      "content": "实践是提高编程能力的关键，多写代码，多思考，多总结。",
      "like_count": 125,
      "time": "2023-06-17 08:15:42"
    }
  ]
}'
```

## 响应示例

```json
{
  "id": 123,
  "title": "如何提高编程能力？",
  "content": "<p>编程能力的提高需要多方面的努力，包括理论学习、实践练习和代码复盘...</p>",
  "publish_time": "2023-06-15",
  "answer_url": "https://example.com/answer/123456",
  "author": "技术达人",
  "author_url": "https://example.com/user/tech_master",
  "author_field": "计算机科学",
  "author_cert": "认证专家",
  "author_fans": 5000,
  "year": 2023,
  "task_id": 1,
  "comments_structured": [
    {
      "author": "Arlene Ran",
      "author_url": "https://www.zhihu.com/people/arlene-ran",
      "content": "给你免费做了个心肺复苏，还不赶紧谢谢人家[酷]",
      "like_count": 87,
      "time": "2023-06-16 14:29:20"
    },
    {
      "author": "倾译",
      "author_url": "https://www.zhihu.com/people/liu-ba-75",
      "content": "<p>我的天，都砸吐了啊，这威力真大</p>",
      "like_count": 37,
      "time": "2023-06-17 00:57:37"
    },
    {
      "author": "程序员小王",
      "author_url": "https://www.zhihu.com/people/programmer_wang",
      "content": "实践是提高编程能力的关键，多写代码，多思考，多总结。",
      "like_count": 125,
      "time": "2023-06-17 08:15:42"
    }
  ]
}
```

## 注意事项

1. `answer_url` 必须是唯一的，如果已存在相同URL的数据，会返回400错误
2. `task_id` 必须对应一个已存在的任务，否则会返回400错误
3. `year` 字段用于确定数据存储在哪个分表中
4. `comments_structured` 是可选字段，如果不提供，则不会创建评论数据
5. 评论数据会自动存储到对应年份的评论分表中
