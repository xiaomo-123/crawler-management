from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.recommendation import recommendation_service
from pydantic import BaseModel

router = APIRouter(prefix="/api/recommendations", tags=["推荐页URL"])

# Pydantic模型
class RecommendationInitResponse(BaseModel):
    success: bool
    message: str
    count: int

class RecommendationCheckResponse(BaseModel):
    exists: bool
    count: int

class RecommendationURLsResponse(BaseModel):
    urls: List[str]
    count: int

# 初始化推荐页URL缓存（从raw_data加载）
@router.post("/init", response_model=RecommendationInitResponse)
async def init_recommendation_cache(db: Session = Depends(get_db)):
    """
    初始化推荐页URL缓存
    1. 清空现有缓存
    2. 从raw_data表加载所有answer_url到Redis
    """
    count = recommendation_service.load_from_raw_data(db)
    return {
        "success": True,
        "message": f"成功加载 {count} 个URL到缓存",
        "count": count
    }

# 检查缓存是否存在
@router.get("/check", response_model=RecommendationCheckResponse)
async def check_recommendation_cache():
    """
    检查推荐页URL缓存是否存在
    """
    exists = recommendation_service.cache_exists()
    count = recommendation_service.get_url_count()
    return {
        "exists": exists,
        "count": count
    }

# 获取推荐页URL（从Redis缓存中获取）
@router.get("/urls", response_model=RecommendationURLsResponse)
async def get_recommendation_urls(count: Optional[int] = 10):
    """
    获取推荐页URL
    - count: 获取的URL数量，默认10个
    """
    if count <= 0:
        raise HTTPException(status_code=400, detail="count必须大于0")

    if count > 100:
        raise HTTPException(status_code=400, detail="count不能超过100")

    urls = recommendation_service.get_random_urls(count)

    if not urls:
        raise HTTPException(status_code=404, detail="缓存中没有URL数据，请先初始化")

    return {
        "urls": urls,
        "count": len(urls)
    }

# 清空推荐页URL缓存
@router.delete("/clear", response_model=dict)
async def clear_recommendation_cache():
    """
    清空推荐页URL缓存
    """
    success = recommendation_service.clear_cache()
    return {
        "success": success,
        "message": "缓存已清空" if success else "清空缓存失败"
    }

# 检查URL并添加到队列
@router.post("/queue/add", response_model=dict)
async def add_url_to_queue(url: str):
    """
    检查URL是否在推荐页URL缓存中，不存在则添加到队列
    """
    from app.utils.redis import get_redis
    from app.config import settings
    
    redis_client = get_redis()
    if not redis_client:
        raise HTTPException(status_code=500, detail="Redis连接失败")
    
    # 检查URL是否已存在
    exists = redis_client.sismember(settings.REDIS_RECOMMENDATION_URLS_KEY, url)
    
    if not exists:
        # 添加到队列
        redis_client.rpush(settings.REDIS_RECOMMENDATION_QUEUE_KEY, url)
        return {
            "success": True,
            "message": "URL已添加到队列",
            "exists": False
        }
    
    return {
        "success": True,
        "message": "URL已存在于缓存中",
        "exists": True
    }

# 处理队列中的URL
@router.post("/queue/process", response_model=dict)
async def process_queue(batch_size: int = 1):
    """
    处理队列中的URL
    """
    from app.utils.redis import get_redis
    from app.config import settings
    
    if batch_size <= 0:
        raise HTTPException(status_code=400, detail="batch_size必须大于0")
    
    if batch_size > 100:
        raise HTTPException(status_code=400, detail="batch_size不能超过100")
    
    redis_client = get_redis()
    if not redis_client:
        raise HTTPException(status_code=500, detail="Redis连接失败")
    
    # 从队列中获取URL
    urls = redis_client.lrange(settings.REDIS_RECOMMENDATION_QUEUE_KEY, 0, batch_size - 1)
    
    if urls:
        # 删除已获取的URL
        redis_client.ltrim(settings.REDIS_RECOMMENDATION_QUEUE_KEY, batch_size, -1)
        return {
            "success": True,
            "processed": len(urls),
            "urls": [url.decode() if isinstance(url, bytes) else url for url in urls]
        }
    
    return {
        "success": True,
        "processed": 0,
        "urls": []
    }
