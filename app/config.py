
import os
from typing import Optional

class Settings:
    # 应用配置
    APP_NAME: str = "小鲸鱼管理系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    PORT: int = 5432

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./crawler_management.db"

    # Redis配置
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # CORS配置
    CORS_ORIGINS: list = ["*"]

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # 小鲸鱼配置
    CRAWLER_DELAY: float = 1.0  # 请求间隔(秒)
    MAX_RETRIES: int = 3        # 最大重试次数
    TIMEOUT: int = 30           # 请求超时时间(秒)

    # 抽样配置
    TOTAL_SAMPLE_NUM: int = 10000  # 总抽样条数

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Redis键定义
    REDIS_RECOMMENDATION_URLS_KEY: str = "recommendation:urls"  # 推荐页URL集合
    REDIS_QA_CRAWLER_URLS_KEY: str = "qa_crawler:urls"  # 问答小鲸鱼URL集合
    REDIS_QA_CRAWLER_QUEUE_KEY: str = "qa_crawler:queue"  # 问答小鲸鱼数据队列
    REDIS_RECOMMENDATION_QUEUE_KEY: str = "recommendation:queue"  # 推荐页数据队列

settings = Settings()
