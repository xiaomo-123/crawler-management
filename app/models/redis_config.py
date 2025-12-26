
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class RedisConfig(Base):
    """Redis配置表"""
    __tablename__ = "redis_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="配置名称")
    host = Column(String(100), nullable=False, default="127.0.0.1", comment="Redis主机地址")
    port = Column(Integer, nullable=False, default=6379, comment="Redis端口")
    db = Column(Integer, nullable=False, default=0, comment="Redis数据库")
    password = Column(String(100), nullable=True, comment="Redis密码")
    is_default = Column(Boolean, nullable=False, default=False, comment="是否为默认配置")
