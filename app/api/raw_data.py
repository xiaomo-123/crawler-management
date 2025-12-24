
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.raw_data import RawData
from pydantic import BaseModel

router = APIRouter(prefix="/api/raw-data", tags=["原始数据"])

# Pydantic模型
class RawDataBase(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    answer_url: str
    author: Optional[str] = None
    author_url: Optional[str] = None
    author_field: Optional[str] = None
    author_cert: Optional[str] = None
    author_fans: Optional[int] = None
    year: int
    task_id: int

class RawDataCreate(RawDataBase):
    pass

class RawDataUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    author_field: Optional[str] = None
    author_cert: Optional[str] = None
    author_fans: Optional[int] = None

class RawDataResponse(RawDataBase):
    id: int

    class Config:
        from_attributes = True

# API路由
@router.get("/", response_model=List[RawDataResponse])
async def get_raw_data(skip: int = 0, limit: int = 100, year: Optional[int] = None, task_id: Optional[int] = None, db: Session = Depends(get_db)):
    """获取原始数据列表"""
    query = db.query(RawData)

    # 按年份过滤
    if year is not None:
        query = query.filter(RawData.year == year)

    # 按任务ID过滤
    if task_id is not None:
        query = query.filter(RawData.task_id == task_id)

    raw_data = query.offset(skip).limit(limit).all()
    return raw_data

@router.get("/{data_id}", response_model=RawDataResponse)
async def get_raw_data_item(data_id: int, db: Session = Depends(get_db)):
    """获取单个原始数据"""
    data = db.query(RawData).filter(RawData.id == data_id).first()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"原始数据ID {data_id} 不存在"
        )
    return data

@router.post("/", response_model=RawDataResponse, status_code=status.HTTP_201_CREATED)
async def create_raw_data(raw_data: RawDataCreate, db: Session = Depends(get_db)):
    """创建新原始数据"""
    # 检查answer_url是否已存在
    existing_data = db.query(RawData).filter(RawData.answer_url == raw_data.answer_url).first()
    if existing_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="回答链接已存在"
        )

    # 检查任务是否存在
    from app.models.task import Task
    task = db.query(Task).filter(Task.id == raw_data.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务ID {raw_data.task_id} 不存在"
        )

    # # 检查年份是否在合理范围内
    # if raw_data.year < 2018 or raw_data.year > 2025:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="年份必须在2018-2025之间"
    #     )

    new_data = RawData(**raw_data.model_dump())
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data

@router.put("/{data_id}", response_model=RawDataResponse)
async def update_raw_data(data_id: int, data_update: RawDataUpdate, db: Session = Depends(get_db)):
    """更新原始数据"""
    db_data = db.query(RawData).filter(RawData.id == data_id).first()
    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"原始数据ID {data_id} 不存在"
        )

    # 更新数据信息
    update_data = data_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_data, key, value)

    db.commit()
    db.refresh(db_data)
    return db_data

@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_raw_data(data_id: int, db: Session = Depends(get_db)):
    """删除原始数据"""
    db_data = db.query(RawData).filter(RawData.id == data_id).first()
    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"原始数据ID {data_id} 不存在"
        )

    db.delete(db_data)
    db.commit()
    return None

@router.get("/stats/by-year")
async def get_raw_data_stats_by_year(db: Session = Depends(get_db)):
    """按年份统计原始数据"""
    from sqlalchemy import func

    stats = db.query(
        RawData.year,
        func.count(RawData.id).label("count")
    ).group_by(RawData.year).all()

    return {str(year): count for year, count in stats}

@router.get("/stats/by-task")
async def get_raw_data_stats_by_task(db: Session = Depends(get_db)):
    """按任务统计原始数据"""
    from sqlalchemy import func
    from app.models.task import Task

    stats = db.query(
        RawData.task_id,
        Task.task_name,
        func.count(RawData.id).label("count")
    ).join(Task).group_by(RawData.task_id, Task.task_name).all()

    return {str(task_id): {"task_name": task_name, "count": count} for task_id, task_name, count in stats}
