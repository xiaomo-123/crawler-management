# 推荐页队列API示例

## 1. 检查URL并添加到队列

### 请求
```bash
curl -X POST "http://localhost:8000/api/recommendations/queue/add?url=https://example.com/article/123"
```

### 响应（URL不存在）
```json
{
  "success": true,
  "message": "URL已添加到队列",
  "exists": false
}
```

### 响应（URL已存在）
```json
{
  "success": true,
  "message": "URL已存在于缓存中",
  "exists": true
}
```

## 2. 处理队列中的URL

### 请求（默认处理10个URL）
```bash
curl -X POST "http://localhost:8000/api/recommendations/queue/process"
```

### 请求（处理20个URL）
```bash
curl -X POST "http://localhost:8000/api/recommendations/queue/process?batch_size=20"
```

### 响应（有URL处理）
```json
{
  "success": true,
  "processed": 10,
  "urls": [
    "https://example.com/article/1",
    "https://example.com/article/2",
    "https://example.com/article/3"
  ]
}
```

### 响应（队列为空）
```json
{
  "success": true,
  "processed": 0,
  "urls": []
}
```
