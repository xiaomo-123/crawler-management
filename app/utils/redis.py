
import redis
from app.config import settings
from app.database import SessionLocal
from app.models.redis_config import RedisConfig

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
