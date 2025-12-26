
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.redis_config import RedisConfig
from pydantic import BaseModel

router = APIRouter(prefix="/api/redis-configs", tags=["Redis配置"])

# Pydantic模型
class RedisConfigBase(BaseModel):
    name: str
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    is_default: bool = False

class RedisConfigCreate(RedisConfigBase):
    pass

class RedisConfigUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    db: Optional[int] = None
    password: Optional[str] = None
    is_default: Optional[bool] = None

class RedisConfigResponse(RedisConfigBase):
    id: int

    class Config:
        orm_mode = True

class RedisConfigTest(BaseModel):
    host: str
    port: int
    db: int
    password: Optional[str] = None

# 获取所有Redis配置
@router.get("/", response_model=List[RedisConfigResponse])
async def get_redis_configs(db: Session = Depends(get_db)):
    """获取所有Redis配置"""
    configs = db.query(RedisConfig).all()
    return configs

# 获取默认Redis配置
@router.get("/default", response_model=Optional[RedisConfigResponse])
async def get_default_redis_config(db: Session = Depends(get_db)):
    """获取默认Redis配置"""
    config = db.query(RedisConfig).filter(RedisConfig.is_default == True).first()
    return config

# 创建Redis配置
@router.post("/", response_model=RedisConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_redis_config(config: RedisConfigCreate, db: Session = Depends(get_db)):
    """创建Redis配置"""
    # 如果设置为默认配置，先将其他配置的is_default设为False
    if config.is_default:
        db.query(RedisConfig).update({"is_default": False})

    db_config = RedisConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

# 更新Redis配置
@router.put("/{config_id}", response_model=RedisConfigResponse)
async def update_redis_config(
    config_id: int, 
    config_update: RedisConfigUpdate, 
    db: Session = Depends(get_db)
):
    """更新Redis配置"""
    db_config = db.query(RedisConfig).filter(RedisConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Redis配置不存在")

    # 如果设置为默认配置，先将其他配置的is_default设为False
    update_data = config_update.dict(exclude_unset=True)
    if update_data.get("is_default") == True:
        db.query(RedisConfig).filter(RedisConfig.id != config_id).update({"is_default": False})

    for field, value in update_data.items():
        setattr(db_config, field, value)

    db.commit()
    db.refresh(db_config)
    return db_config

# 删除Redis配置
@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_redis_config(config_id: int, db: Session = Depends(get_db)):
    """删除Redis配置"""
    db_config = db.query(RedisConfig).filter(RedisConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Redis配置不存在")

    db.delete(db_config)
    db.commit()
    return None

# 测试Redis连接
@router.post("/test", status_code=status.HTTP_200_OK)
async def test_redis_connection(config: RedisConfigTest):
    """测试Redis连接"""
    import redis

    try:
        # 创建连接池
        pool = redis.ConnectionPool(
            host=config.host,
            port=config.port,
            db=config.db,
            password=config.password,
            decode_responses=True
        )

        # 创建客户端
        client = redis.Redis(connection_pool=pool)

        # 测试连接
        client.ping()

        return {"success": True, "message": "Redis连接成功"}
    except Exception as e:
        return {"success": False, "message": f"Redis连接失败: {str(e)}"}
