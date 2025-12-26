
from fastapi import APIRouter
from app.utils.redis import reload_redis

router = APIRouter(prefix="/api/utils", tags=["工具"])

@router.post("/reload-redis")
async def reload_redis_config():
    """重新加载Redis配置"""
    try:
        result = reload_redis()
        if result:
            return {"success": True, "message": "Redis配置重新加载成功"}
        else:
            return {"success": False, "message": "Redis配置重新加载失败"}
    except Exception as e:
        return {"success": False, "message": f"Redis配置重新加载失败: {str(e)}"}
