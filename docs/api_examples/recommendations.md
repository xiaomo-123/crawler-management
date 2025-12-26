# 推荐页URL API文档

## API列表

### 1. 初始化推荐页URL缓存

**接口描述**: 初始化推荐页URL缓存，会先清空现有缓存，然后从raw_data表加载所有answer_url到Redis

**请求方式**: POST

**请求路径**: `/api/recommendations/init`

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
curl -X POST "http://localhost:8000/api/recommendations/init"   -H "Content-Type: application/json"
```

---

### 2. 检查缓存是否存在

**接口描述**: 检查推荐页URL缓存是否存在，并返回缓存的URL数量

**请求方式**: GET

**请求路径**: `/api/recommendations/check`

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
curl -X GET "http://localhost:8000/api/recommendations/check"   -H "Content-Type: application/json"
```

---

### 3. 获取推荐页URL

**接口描述**: 从Redis缓存中随机获取指定数量的推荐页URL

**请求方式**: GET

**请求路径**: `/api/recommendations/urls`

**请求参数**:
- `count` (可选): 获取的URL数量，默认10个，最大100个

**响应示例**:
```json
{
  "urls": [
    "https://example.com/answer/1",
    "https://example.com/answer/2",
    "https://example.com/answer/3"
  ],
  "count": 3
}
```

**curl示例**:
```bash
# 获取默认10个URL
curl -X GET "http://localhost:8000/api/recommendations/urls"   -H "Content-Type: application/json"

# 获取20个URL
curl -X GET "http://localhost:8000/api/recommendations/urls?count=20"   -H "Content-Type: application/json"
```

---

### 4. 清空推荐页URL缓存

**接口描述**: 清空推荐页URL的Redis缓存

**请求方式**: DELETE

**请求路径**: `/api/recommendations/clear`

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
curl -X DELETE "http://localhost:8000/api/recommendations/clear"   -H "Content-Type: application/json"
```

---

## 使用流程

1. **初始化缓存**: 首次使用时，调用初始化接口从raw_data表加载URL到Redis
   ```bash
   curl -X POST "http://localhost:8000/api/recommendations/init"
   ```

2. **检查缓存**: 确认缓存是否存在
   ```bash
   curl -X GET "http://localhost:8000/api/recommendations/check"
   ```

3. **获取URL**: 从缓存中获取推荐页URL
   ```bash
   curl -X GET "http://localhost:8000/api/recommendations/urls?count=10"
   ```

4. **清空缓存**: 如需重新加载，可先清空缓存
   ```bash
   curl -X DELETE "http://localhost:8000/api/recommendations/clear"
   ```
