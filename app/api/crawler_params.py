from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.crawler_param import CrawlerParam

router = APIRouter(prefix="/api/crawler-params", tags=["爬虫参数"])


@router.get("/", response_model=List[dict])
async def get_crawler_params(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """获取爬虫参数列表"""
    params = db.query(CrawlerParam).offset(skip).limit(limit).all()
    total = db.query(CrawlerParam).count()

    result = []
    for param in params:
        result.append({
            "id": param.id,
            "url": param.url,
            "api_request": param.api_request,
            "task_type": param.task_type,
            "start_time": param.start_time,
            "end_time": param.end_time,
            "interval_time": param.interval_time,
            "error_count": param.error_count,
            "restart_browser_time": param.restart_browser_time,
            "created_at": param.created_at.strftime("%Y-%m-%d %H:%M:%S") if param.created_at else None,
            "updated_at": param.updated_at.strftime("%Y-%m-%d %H:%M:%S") if param.updated_at else None
        })

    return result


@router.get("/{param_id}", response_model=dict)
async def get_crawler_param(param_id: int, db: Session = Depends(get_db)):
    """获取单个爬虫参数"""
    param = db.query(CrawlerParam).filter(CrawlerParam.id == param_id).first()
    if not param:
        raise HTTPException(status_code=404, detail="爬虫参数不存在")

    return {
        "id": param.id,
        "url": param.url,
        "api_request": param.api_request,
        "task_type": param.task_type,
        "start_time": param.start_time,
        "end_time": param.end_time,
        "interval_time": param.interval_time,
        "error_count": param.error_count,
        "restart_browser_time": param.restart_browser_time,
        "created_at": param.created_at.strftime("%Y-%m-%d %H:%M:%S") if param.created_at else None,
        "updated_at": param.updated_at.strftime("%Y-%m-%d %H:%M:%S") if param.updated_at else None
    }


@router.post("/")
async def create_crawler_param(param_data: dict, db: Session = Depends(get_db)):
    """创建爬虫参数"""
    try:
        # 处理时间字段(小时数)
        start_time = param_data.get("start_time", 0)
        end_time = param_data.get("end_time", 23)

        # 验证时间范围
        if not (0 <= start_time <= 23):
            raise HTTPException(status_code=400, detail="开始时间必须在0-23之间")
        if not (0 <= end_time <= 23):
            raise HTTPException(status_code=400, detail="结束时间必须在0-23之间")

        param = CrawlerParam(
            url=param_data["url"],
            api_request=param_data["api_request"],
            task_type=param_data["task_type"],
            start_time=start_time,
            end_time=end_time,
            interval_time=param_data.get("interval_time", 1),
            error_count=param_data.get("error_count", 3),
            restart_browser_time=param_data.get("restart_browser_time", 24)
        )

        db.add(param)
        db.commit()
        db.refresh(param)

        return {"id": param.id, "message": "爬虫参数创建成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{param_id}")
async def update_crawler_param(param_id: int, param_data: dict, db: Session = Depends(get_db)):
    """更新爬虫参数"""
    try:
        param = db.query(CrawlerParam).filter(CrawlerParam.id == param_id).first()
        if not param:
            raise HTTPException(status_code=404, detail="爬虫参数不存在")

        # 更新字段
        if "url" in param_data:
            param.url = param_data["url"]
        if "api_request" in param_data:
            param.api_request = param_data["api_request"]
        if "task_type" in param_data:
            param.task_type = param_data["task_type"]
        if "start_time" in param_data:
            start_time = param_data["start_time"]
            if start_time is not None and not (0 <= start_time <= 23):
                raise HTTPException(status_code=400, detail="开始时间必须在0-23之间")
            param.start_time = start_time
        if "end_time" in param_data:
            end_time = param_data["end_time"]
            if end_time is not None and not (0 <= end_time <= 23):
                raise HTTPException(status_code=400, detail="结束时间必须在0-23之间")
            param.end_time = end_time
        if "interval_time" in param_data:
            param.interval_time = param_data["interval_time"]
        if "error_count" in param_data:
            param.error_count = param_data["error_count"]
        if "restart_browser_time" in param_data:
            param.restart_browser_time = param_data["restart_browser_time"]

        db.commit()

        return {"message": "爬虫参数更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{param_id}")
async def delete_crawler_param(param_id: int, db: Session = Depends(get_db)):
    """删除爬虫参数"""
    try:
        param = db.query(CrawlerParam).filter(CrawlerParam.id == param_id).first()
        if not param:
            raise HTTPException(status_code=404, detail="爬虫参数不存在")

        db.delete(param)
        db.commit()

        return {"message": "爬虫参数删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
