
import redis
from app.config import settings

# 全局Redis连接池
_redis_pool = None
_redis_client = None

def get_redis():
    """获取Redis客户端"""
    global _redis_pool, _redis_client

    if _redis_client is None:
        # 创建连接池
        _redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
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

    return _redis_client

def init_redis():
    """初始化Redis连接"""
    global _redis_pool, _redis_client

    try:
        # 创建连接池
        _redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

        # 创建客户端
        _redis_client = redis.Redis(connection_pool=_redis_pool)

        # 测试连接
        _redis_client.ping()
        print("Redis初始化成功")
        return True
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
