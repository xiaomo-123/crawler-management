from sqlalchemy.orm import Session
from app.utils.redis import get_redis
from app.models.raw_data import RawData
from typing import List, Optional

class RecommendationService:
    """推荐页URL服务"""

    REDIS_KEY = "recommendation:urls"

    def __init__(self):
        self.redis_client = None

    def _get_redis(self):
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = get_redis()
        return self.redis_client

    def clear_cache(self) -> bool:
        """清空推荐页URL的Redis缓存"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                redis_client.delete(self.REDIS_KEY)
                return True
            return False
        except Exception as e:
            print(f"清空Redis缓存失败: {str(e)}")
            return False

    def load_from_raw_data(self, db: Session) -> int:
        """从raw_data表加载所有answer_url到Redis缓存"""
        try:
            # 清空现有缓存
            self.clear_cache()

            # 从数据库获取所有answer_url
            urls = db.query(RawData.answer_url).all()
            url_list = [url[0] for url in urls if url[0]]

            if not url_list:
                return 0

            # 写入Redis
            redis_client = self._get_redis()
            if redis_client:
                redis_client.sadd(self.REDIS_KEY, *url_list)
                return len(url_list)
            return 0
        except Exception as e:
            print(f"加载URL到Redis失败: {str(e)}")
            return 0

    def get_url_count(self) -> int:
        """获取Redis中缓存的URL数量"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                return redis_client.scard(self.REDIS_KEY)
            return 0
        except Exception as e:
            print(f"获取URL数量失败: {str(e)}")
            return 0

    def cache_exists(self) -> bool:
        """检查Redis缓存是否存在"""
        return self.get_url_count() > 0

    def get_random_urls(self, count: int = 10) -> List[str]:
        """从Redis缓存中随机获取指定数量的URL"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                return redis_client.srandmember(self.REDIS_KEY, count)
            return []
        except Exception as e:
            print(f"获取随机URL失败: {str(e)}")
            return []

# 创建服务实例
recommendation_service = RecommendationService()
