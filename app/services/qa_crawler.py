from sqlalchemy.orm import Session
from app.utils.redis import get_redis
from app.models.raw_data import RawData
from app.models.comment_data import CommentDataFactory
from app.config import settings
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

class QACrawlerService:
    """问答爬虫服务"""

    # Redis键定义（从config.py统一管理）
    REDIS_URL_KEY = settings.REDIS_QA_CRAWLER_URLS_KEY  # 存储所有URL的集合
    REDIS_QUEUE_KEY = settings.REDIS_QA_CRAWLER_QUEUE_KEY  # 存储待处理数据的队列
    REDIS_RECOMMENDATION_KEY = settings.REDIS_RECOMMENDATION_URLS_KEY  # 推荐页URL集合

    def __init__(self):
        self.redis_client = None

    def _get_redis(self):
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = get_redis()
        return self.redis_client

    def clear_cache(self) -> bool:
        """清空问答爬虫的Redis缓存"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                redis_client.delete(self.REDIS_URL_KEY)
                redis_client.delete(self.REDIS_QUEUE_KEY)
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
                redis_client.sadd(self.REDIS_URL_KEY, *url_list)
                return len(url_list)
            return 0
        except Exception as e:
            print(f"加载URL到Redis失败: {str(e)}")
            return 0

    def url_exists(self, url: str) -> bool:
        """检查URL是否已存在于缓存中"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                return redis_client.sismember(self.REDIS_URL_KEY, url)
            return False
        except Exception as e:
            print(f"检查URL存在性失败: {str(e)}")
            return False

    def add_url(self, url: str) -> bool:
        """添加URL到缓存"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                redis_client.sadd(self.REDIS_URL_KEY, url)
                return True
            return False
        except Exception as e:
            print(f"添加URL到缓存失败: {str(e)}")
            return False

    def add_to_queue(self, data: Dict[str, Any]) -> bool:
        """添加数据到生产队列"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                # 将数据序列化为JSON并推入队列
                redis_client.rpush(self.REDIS_QUEUE_KEY, json.dumps(data, ensure_ascii=False))
                return True
            return False
        except Exception as e:
            print(f"添加数据到队列失败: {str(e)}")
            return False

    def get_queue_size(self) -> int:
        """获取队列大小"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                return redis_client.llen(self.REDIS_QUEUE_KEY)
            return 0
        except Exception as e:
            print(f"获取队列大小失败: {str(e)}")
            return 0

    def get_from_queue(self, count: int = 1) -> List[Dict[str, Any]]:
        """从队列中获取数据"""
        try:
            redis_client = self._get_redis()
            if redis_client:
                # 从队列左侧弹出数据
                items = redis_client.lrange(self.REDIS_QUEUE_KEY, 0, count - 1)
                if items:
                    # 删除已获取的数据
                    redis_client.ltrim(self.REDIS_QUEUE_KEY, count, -1)
                    return [json.loads(item) for item in items]
            return []
        except Exception as e:
            print(f"从队列获取数据失败: {str(e)}")
            return []

    def save_to_database(self, data: Dict[str, Any], db: Session) -> Optional[int]:
        """将数据保存到数据库（raw_data和comment_data子表）"""
        try:
            # 提取年月信息
            publish_time = data.get('publish_time', '')
            year = data.get('year', datetime.now().year)

            # 解析年月
            if publish_time:
                try:
                    dt = datetime.strptime(publish_time, '%Y-%m-%d')
                    year = dt.year
                    month = dt.month
                except:
                    month = 1
            else:
                month = 1

            # 创建raw_data记录
            raw_data = RawData(
                title=data.get('title'),
                content=data.get('content'),
                publish_time=publish_time,
                answer_url=data.get('url'),
                author=data.get('author'),
                author_url=data.get('author_url'),
                author_field=data.get('author_field'),
                author_cert=data.get('author_cert'),
                author_fans=data.get('author_fans'),
                year=year,
                task_id=data.get('task_id', 1)  # 默认任务ID为1
            )

            db.add(raw_data)
            db.flush()  # 获取ID但不提交

            # 获取对应的评论分表模型
            comment_model = CommentDataFactory.get_model(year, month)

            # 保存评论数据
            comments = data.get('comments_structured', [])
            for comment in comments:
                comment_record = comment_model(
                    author=comment.get('author'),
                    author_url=comment.get('author_url'),
                    content=comment.get('content'),
                    like_count=comment.get('like_count'),
                    time=comment.get('time'),
                    raw_data_id=raw_data.id,
                    year=year,
                    month=month
                )
                db.add(comment_record)

            db.commit()
            return raw_data.id
        except Exception as e:
            db.rollback()
            print(f"保存数据到数据库失败: {str(e)}")
            return None

    def get_urls(self, count: Optional[int] = None) -> List[str]:
        """从Redis缓存中获取URL
        
        Args:
            count: 要获取的URL数量，如果为None则获取所有URL
        
        Returns:
            URL列表
        """
        try:
            redis_client = self._get_redis()
            if redis_client:
                if count is None:
                    # 获取所有URL
                    return list(redis_client.smembers(self.REDIS_URL_KEY))
                else:
                    # 随机获取指定数量的URL
                    return list(redis_client.srandmember(self.REDIS_URL_KEY, count))
            return []
        except Exception as e:
            print(f"获取URL失败: {str(e)}")
            return []

    def process_queue(self, db: Session, batch_size: int = 10) -> Dict[str, int]:
        """处理队列中的数据，批量保存到数据库"""
        try:
            processed = 0
            failed = 0

            while True:
                # 从队列获取一批数据
                items = self.get_from_queue(batch_size)
                if not items:
                    break

                for item in items:
                    if self.save_to_database(item, db):
                        processed += 1
                    else:
                        failed += 1

            return {
                "processed": processed,
                "failed": failed
            }
        except Exception as e:
            print(f"处理队列失败: {str(e)}")
            return {
                "processed": 0,
                "failed": 0
            }

# 创建服务实例
qa_crawler_service = QACrawlerService()
