# 原始数据与评论数据的关联关系分析

## 概述

本系统采用了分表设计，将原始数据(raw_data)和评论数据(comments_structured)分别按年份存储在不同的表中，通过外键关联实现数据关联。

## 表结构设计

### 1. 原始数据表 (raw_data)

原始数据按年份分表存储，表名格式为 `raw_data_YYYY`，例如：
- raw_data_2023
- raw_data_2024

主要字段：
- id: 主键，自增
- title: 标题
- content: 内容
- answer_url: 回答链接（唯一）
- author: 作者
- author_url: 作者链接
- author_field: 作者领域
- author_cert: 作者认证
- author_fans: 作者粉丝数
- year: 年份（用于分表）
- task_id: 关联任务ID

### 2. 评论数据表 (comment_data)

评论数据也按年份分表存储，表名格式为 `comment_data_YYYY`，例如：
- comment_data_2023
- comment_data_2024

主要字段：
- id: 主键，自增
- author: 评论作者
- author_url: 作者链接
- content: 评论内容
- like_count: 点赞数
- time: 评论时间
- raw_data_id: 关联的原始数据ID（外键）
- year: 年份（用于分表）

## 关联关系

原始数据与评论数据通过 `raw_data_id` 字段建立一对多关系：
- 一条原始数据可以有多条评论
- 每条评论只关联一条原始数据

为了确保查询的完整性，关联关系需要满足以下条件：
1. 评论表中的 `raw_data_id` 必须对应原始数据表中的 `id`
2. 查询时需要同时使用年份和ID两个条件，确保数据匹配

```
raw_data_2023 (1) -----> (N) comment_data_2023
       id                      raw_data_id
       year                    year
```

### 唯一标识

每条数据的唯一标识由 `(year, id)` 组成：
- 原始数据：`(year, raw_data_id)`
- 评论数据：`(year, id)`

这种设计确保了即使不同年份的表中有相同的ID，也能通过年份区分，保证数据唯一性。

## 数据流转

### 1. 创建数据流程

当创建包含评论的原始数据时：

1. 首先将原始数据插入到对应年份的raw_data表中
2. 获取新插入的原始数据的ID
3. 将每条评论数据转换为包含raw_data_id的对象
4. 将评论数据批量插入到对应年份的comment_data表中

代码实现（来自API）：
```python
# 1. 插入原始数据
success = RawDataManager.insert_data(data_dict)

# 2. 获取新插入数据的ID
latest_data = RawDataManager.query_data(years=[raw_data.year], limit=1)
new_data = latest_data[0]

# 3. 处理评论数据
if comments and len(comments) > 0:
    comment_data_list = []
    for comment in comments:
        comment_data = {
            'author': comment.get('author'),
            'author_url': comment.get('author_url'),
            'content': comment.get('content'),
            'like_count': comment.get('like_count'),
            'time': comment.get('time'),
            'raw_data_id': new_data.get('id'),  # 关联原始数据ID
            'year': raw_data.year
        }
        comment_data_list.append(comment_data)

    # 4. 批量插入评论数据
    CommentDataManager.batch_insert_data(comment_data_list)
```

### 2. 查询数据流程

当查询原始数据及其评论时：

1. 根据ID和年份在对应的raw_data表中查找原始数据
2. 使用原始数据的ID和年份在comment_data表中查找相关评论

代码实现（来自API）：
```python
# 查询原始数据 - 使用年份和ID两个条件确保准确性
for year in years:
    model = RawDataFactory.get_model(year)
    item = db.query(model).filter(model.id == data_id, model.year == year).first()
    if item:
        data = item
        break

# 查询评论数据 - 同时使用年份和原始数据ID确保关联正确
comments = CommentDataManager.query_data(years=[data.year], raw_data_id=data_id)
```

### 查询优化

为了提高查询效率，建议在以下字段上创建复合索引：

1. 原始数据表：
   - `(year, id)` - 用于快速定位特定年份的特定记录
   - `(year, task_id)` - 用于按任务和年份查询

2. 评论数据表：
   - `(year, raw_data_id)` - 用于快速查找特定原始数据的所有评论
   - `(year, id)` - 用于唯一标识评论记录

```sql
-- 原始数据表索引
CREATE INDEX idx_raw_data_year_id ON raw_data_2023 (year, id);
CREATE INDEX idx_raw_data_year_task ON raw_data_2023 (year, task_id);

-- 评论数据表索引
CREATE INDEX idx_comment_year_raw_id ON comment_data_2023 (year, raw_data_id);
CREATE INDEX idx_comment_year_id ON comment_data_2023 (year, id);
```

## 分表策略的优势

1. **性能优化**：通过按年份分表，减少了单表数据量，提高了查询效率
2. **易于维护**：不同年份的数据分开存储，便于数据归档和管理
3. **扩展性强**：可以根据需要增加新的分表维度，如按月份分表

## 注意事项

1. **数据一致性**：原始数据和评论数据的年份必须一致，否则无法正确关联
2. **查询复杂性**：跨表查询需要处理多个年份的表，增加了查询复杂度
3. **ID管理**：不同年份的表可能有相同的ID，需要结合年份和ID进行唯一标识

## 优化建议

1. **添加复合索引**：
   - 在raw_data表上添加(year, id)和(year, task_id)复合索引
   - 在comment_data表上添加(year, raw_data_id)和(year, id)复合索引
   - 提高关联查询效率，确保数据完整性

2. **查询完整性保证**：
   - 所有查询操作必须同时使用年份和ID作为条件
   - 应用层添加验证，确保关联数据的年份一致性
   - 考虑添加数据库约束，防止跨年份的数据关联

3. **缓存机制**：
   - 对热点数据添加缓存，减少数据库查询压力
   - 缓存键应包含年份和ID，如"raw_data:2023:123"

4. **异步处理**：
   - 对于大量评论数据的插入，使用异步处理提高响应速度
   - 批量插入时确保同一批次数据的年份一致性

5. **数据校验**：
   - 添加定期检查任务，验证raw_data_id与实际raw_data记录的对应关系
   - 检查并修复可能存在的数据不一致问题
