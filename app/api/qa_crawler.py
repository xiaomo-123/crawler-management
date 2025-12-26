from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.services.qa_crawler import qa_crawler_service
from pydantic import BaseModel, HttpUrl
from datetime import datetime

router = APIRouter(prefix="/api/qa-crawler", tags=["问答小鲸鱼"])

# Pydantic模型
class CommentData(BaseModel):
    """评论数据模型"""
    author: Optional[str] = None
    author_url: Optional[HttpUrl] = None
    content: Optional[str] = None
    like_count: Optional[int] = None
    time: Optional[str] = None

class QACrawlerData(BaseModel):
    """问答小鲸鱼数据模型"""
    rank: Optional[int] = None
    title: Optional[str] = None
    url: HttpUrl
    question_detail: Optional[str] = None
    answer_content_text: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[HttpUrl] = None
    author_field: Optional[str] = None
    author_cert: Optional[str] = None
    author_fans: Optional[int] = None
    year: int
    publish_time: Optional[str] = None
    images: Optional[List[str]] = None
    comments_structured: Optional[List[CommentData]] = None

class InitResponse(BaseModel):
    """初始化响应模型"""
    success: bool
    message: str
    count: int

class CheckResponse(BaseModel):
    """检查响应模型"""
    exists: bool
    count: int

class QueueStatusResponse(BaseModel):
    """队列状态响应模型"""
    queue_size: int
    url_count: int

class ProcessQueueResponse(BaseModel):
    """处理队列响应模型"""
    processed: int
    failed: int

class SubmitResponse(BaseModel):
    """提交响应模型"""
    success: bool
    message: str
    url_exists: bool

# 初始化问答小鲸鱼缓存（从raw_data加载）
@router.post("/init", response_model=InitResponse)
async def init_qa_crawler_cache(db: Session = Depends(get_db)):
    """
    初始化问答小鲸鱼缓存
    1. 清空现有缓存
    2. 从raw_data表加载所有answer_url到Redis
    """
    count = qa_crawler_service.load_from_raw_data(db)
    return {
        "success": True,
        "message": f"成功加载 {count} 个URL到缓存",
        "count": count
    }

# 检查缓存是否存在
@router.get("/check", response_model=CheckResponse)
async def check_qa_crawler_cache():
    """
    检查问答小鲸鱼URL缓存是否存在
    """
    exists = qa_crawler_service.url_exists("dummy") or qa_crawler_service.get_queue_size() > 0
    # 获取实际URL数量
    redis_client = qa_crawler_service._get_redis()
    url_count = redis_client.scard(qa_crawler_service.REDIS_URL_KEY) if redis_client else 0
    return {
        "exists": exists,
        "count": url_count
    }

# 提交问答小鲸鱼数据
@router.post("/submit", response_model=SubmitResponse)
async def submit_qa_crawler_data(data: QACrawlerData):
    """
    提交问答小鲸鱼数据
    1. 检查URL是否已存在于缓存中
    2. 如果不存在，将URL添加到推荐页URL和问答小鲸鱼Redis缓存
    3. 将数据添加到生产队列
    """
    url_str = str(data.url)

    # 检查URL是否已存在
    url_exists = qa_crawler_service.url_exists(url_str)

    if not url_exists:
        # 将URL添加到问答小鲸鱼缓存
        qa_crawler_service.add_url(url_str)

        # 将URL添加到推荐页URL缓存
        from app.services.recommendation import recommendation_service
        recommendation_service.add_url(url_str)

    # 将数据添加到生产队列
    data_dict = data.dict()
    data_dict['url'] = url_str
    if data.author_url:
        data_dict['author_url'] = str(data.author_url)
    if data.comments_structured:
        # 处理评论数据，确保所有URL字段都转换为字符串
        comments_list = []
        for comment in data.comments_structured:
            comment_dict = comment.dict()
            if comment_dict.get('author_url'):
                comment_dict['author_url'] = str(comment_dict['author_url'])
            comments_list.append(comment_dict)
        data_dict['comments_structured'] = comments_list

    qa_crawler_service.add_to_queue(data_dict)

    return {
        "success": True,
        "message": "数据已提交",
        "url_exists": url_exists
    }

# 获取队列状态
@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """
    获取生产队列状态
    """
    queue_size = qa_crawler_service.get_queue_size()
    redis_client = qa_crawler_service._get_redis()
    url_count = redis_client.scard(qa_crawler_service.REDIS_URL_KEY) if redis_client else 0

    return {
        "queue_size": queue_size,
        "url_count": url_count
    }

# 处理队列中的数据
@router.post("/queue/process", response_model=ProcessQueueResponse)
async def process_queue(
    batch_size: int = 10,
    db: Session = Depends(get_db)
):
    """
    处理生产队列中的数据，保存到数据库
    - batch_size: 每批处理的数据量，默认10
    """
    if batch_size <= 0:
        raise HTTPException(status_code=400, detail="batch_size必须大于0")

    if batch_size > 100:
        raise HTTPException(status_code=400, detail="batch_size不能超过100")

    result = qa_crawler_service.process_queue(db, batch_size)
    return result

# 获取问答小鲸鱼URL
@router.get("/urls", response_model=dict)
async def get_qa_crawler_urls(count: Optional[int] = None):
    """
    从Redis缓存中获取问答小鲸鱼URL
    
    参数:
    - count: 要获取的URL数量，如果为None则获取所有URL
    
    返回:
    - urls: URL列表
    - count: 返回的URL数量
    - total: 缓存中URL总数
    
    示例:
    ```bash
    # 获取所有URL
    curl -X GET "http://localhost:8000/api/qa-crawler/urls"
    
    # 获取10个随机URL
    curl -X GET "http://localhost:8000/api/qa-crawler/urls?count=10"
    ```
    """
    # 获取URL
    urls = qa_crawler_service.get_urls(count)
    
    # 获取URL总数
    redis_client = qa_crawler_service._get_redis()
    total = redis_client.scard(qa_crawler_service.REDIS_URL_KEY) if redis_client else 0
    
    return {
        "urls": urls,
        "count": len(urls),
        "total": total
    }

# 清空问答小鲸鱼缓存
@router.delete("/clear", response_model=dict)
async def clear_qa_crawler_cache():
    """
    清空问答小鲸鱼的Redis缓存
    """
    success = qa_crawler_service.clear_cache()
    return {
        "success": success,
        "message": "缓存已清空" if success else "清空缓存失败"
    }
