
import redis
from app.config import settings
from app.database import SessionLocal
from app.models.redis_config import RedisConfig
from app.models.raw_data import RawData

# 全局Redis连接池
_redis_pool = None
_redis_client = None

def get_redis():
    """获取Redis客户端"""
    global _redis_pool, _redis_client

    if _redis_client is None:
        # 从数据库获取Redis配置
        db = SessionLocal()
        try:
            redis_config = db.query(RedisConfig).filter(RedisConfig.is_default == True).first()

            # 如果没有配置，使用默认配置并保存到数据库
            if not redis_config:
                redis_config = RedisConfig(
                    name="默认配置",
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    is_default=True
                )
                db.add(redis_config)
                db.commit()
                db.refresh(redis_config)
                print("已创建默认Redis配置")

            # 创建连接池
            _redis_pool = redis.ConnectionPool(
                host=redis_config.host,
                port=redis_config.port,
                db=redis_config.db,
                password=redis_config.password,
                decode_responses=True
            )

            # 创建客户端
            _redis_client = redis.Redis(connection_pool=_redis_pool)

            # 测试连接
            try:
                _redis_client.ping()
                print("Redis连接成功")
            except Exception as e:
                print(f"Redis连接失败: {str(e)}")
                _redis_client = None
        finally:
            db.close()

    return _redis_client

def init_redis():
    """初始化Redis连接"""
    global _redis_pool, _redis_client

    try:
        # 从数据库获取Redis配置
        db = SessionLocal()
        try:
            redis_config = db.query(RedisConfig).filter(RedisConfig.is_default == True).first()

            # 如果没有配置，使用默认配置并保存到数据库
            if not redis_config:
                redis_config = RedisConfig(
                    name="默认配置",
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    is_default=True
                )
                db.add(redis_config)
                db.commit()
                db.refresh(redis_config)
                print("已创建默认Redis配置")

            # 创建连接池
            _redis_pool = redis.ConnectionPool(
                host=redis_config.host,
                port=redis_config.port,
                db=redis_config.db,
                password=redis_config.password,
                decode_responses=True
            )

            # 创建客户端
            _redis_client = redis.Redis(connection_pool=_redis_pool)

            # 测试连接
            _redis_client.ping()
            print("Redis初始化成功")
            init_recommendation_and_qa_crawler_cache()
            return True
        finally:
            db.close()
    except Exception as e:
        print(f"Redis初始化失败: {str(e)}")
        print("系统将在没有Redis的情况下运行")
        _redis_client = None
        return False

def close_redis():
    """关闭Redis连接"""
    global _redis_pool, _redis_client

    if _redis_client:
        _redis_client.close()
        _redis_client = None

    if _redis_pool:
        _redis_pool.disconnect()
        _redis_pool = None

def reload_redis():
    """重新加载Redis配置"""
    global _redis_pool, _redis_client

    # 先关闭现有连接
    close_redis()

    # 重新初始化
    return init_redis()

def clear_recommendation_and_qa_crawler_cache():
    """清空推荐页URL和问答小鲸鱼的Redis缓存"""
    try:
        redis_client = get_redis()
        if redis_client:
            # 清空推荐页URL缓存
            redis_client.delete(settings.REDIS_RECOMMENDATION_URLS_KEY)
            # 清空问答小鲸鱼URL缓存
            redis_client.delete(settings.REDIS_QA_CRAWLER_URLS_KEY)
            # 清空问答小鲸鱼数据队列
            redis_client.delete(settings.REDIS_QA_CRAWLER_QUEUE_KEY)
            print("已清空推荐页URL和问答小鲸鱼缓存")
            return True
        return False
    except Exception as e:
        print(f"清空缓存失败: {str(e)}")
        return False

def init_recommendation_and_qa_crawler_cache():
    """初始化推荐页URL和问答小鲸鱼缓存，从raw_data表加载所有answer_url"""
    try:
        # 先清空现有缓存
        clear_recommendation_and_qa_crawler_cache()
        
        # 从数据库获取所有answer_url
        db = SessionLocal()
        try:
            urls = db.query(RawData.answer_url).all()
            url_list = [url[0] for url in urls if url[0]]
            
            if not url_list:
                print("没有找到任何answer_url")
                return 0
            
            # 写入Redis
            redis_client = get_redis()
            if redis_client:
                # 添加到推荐页URL集合
                redis_client.sadd(settings.REDIS_RECOMMENDATION_URLS_KEY, *url_list)
                # 添加到问答小鲸鱼URL集合
                redis_client.sadd(settings.REDIS_QA_CRAWLER_URLS_KEY, *url_list)
                print(f"成功加载 {len(url_list)} 个URL到缓存")
                return len(url_list)
            return 0
        finally:
            db.close()
    except Exception as e:
        print(f"初始化缓存失败: {str(e)}")
        return 0
