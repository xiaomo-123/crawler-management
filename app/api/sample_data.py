
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.sample_data import SampleData
from app.models.raw_data import RawData
from app.models.year_quota import YearQuota
from pydantic import BaseModel
import random

router = APIRouter(prefix="/api/sample-data", tags=["抽样数据"])

# Pydantic模型
class SampleDataBase(BaseModel):
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

class SampleDataCreate(SampleDataBase):
    pass

class SampleDataUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    author_field: Optional[str] = None
    author_cert: Optional[str] = None
    author_fans: Optional[int] = None

class SampleDataResponse(SampleDataBase):
    id: int

    class Config:
        from_attributes = True

# API路由
@router.get("/", response_model=List[SampleDataResponse])
async def get_sample_data(skip: int = 0, limit: int = 100, year: Optional[int] = None, task_id: Optional[int] = None, db: Session = Depends(get_db)):
    """获取抽样数据列表"""
    query = db.query(SampleData)

    # 按年份过滤
    if year is not None:
        query = query.filter(SampleData.year == year)

    # 按任务ID过滤
    if task_id is not None:
        query = query.filter(SampleData.task_id == task_id)

    sample_data = query.offset(skip).limit(limit).all()
    return sample_data

@router.get("/{data_id}", response_model=SampleDataResponse)
async def get_sample_data_item(data_id: int, db: Session = Depends(get_db)):
    """获取单个抽样数据"""
    data = db.query(SampleData).filter(SampleData.id == data_id).first()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"抽样数据ID {data_id} 不存在"
        )
    return data

@router.post("/", response_model=SampleDataResponse, status_code=status.HTTP_201_CREATED)
async def create_sample_data(sample_data: SampleDataCreate, db: Session = Depends(get_db)):
    """创建新抽样数据"""
    # 检查answer_url是否已存在
    existing_data = db.query(SampleData).filter(SampleData.answer_url == sample_data.answer_url).first()
    if existing_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="回答链接已存在"
        )

    # 检查任务是否存在
    from app.models.task import Task
    task = db.query(Task).filter(Task.id == sample_data.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务ID {sample_data.task_id} 不存在"
        )

    # 检查年份是否在合理范围内
    if sample_data.year < 2018 or sample_data.year > 2025:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="年份必须在2018-2025之间"
        )

    new_data = SampleData(**sample_data.dict())
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data

@router.put("/{data_id}", response_model=SampleDataResponse)
async def update_sample_data(data_id: int, data_update: SampleDataUpdate, db: Session = Depends(get_db)):
    """更新抽样数据"""
    db_data = db.query(SampleData).filter(SampleData.id == data_id).first()
    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"抽样数据ID {data_id} 不存在"
        )

    # 更新数据信息
    update_data = data_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_data, key, value)

    db.commit()
    db.refresh(db_data)
    return db_data

@router.delete("/clear-all")
async def clear_all_sample_data(db: Session = Depends(get_db)):
    """删除所有抽样数据"""
    try:
        # 使用原生SQL删除所有数据
        db.query(SampleData).delete()
        db.commit()
        return {"message": "所有抽样数据已清空"}
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sample_data(data_id: int, db: Session = Depends(get_db)):
    """删除抽样数据"""
    db_data = db.query(SampleData).filter(SampleData.id == data_id).first()
    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"抽样数据ID {data_id} 不存在"
        )

    db.delete(db_data)
    db.commit()
    return None

@router.post("/sample", status_code=status.HTTP_202_ACCEPTED)
async def sample_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """按配额抽样数据"""
    # 检查是否已有抽样数据
    existing_sample_data = db.query(SampleData).first()
    if existing_sample_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已有抽样数据，请先清空现有数据"
        )

    # 添加后台任务
    background_tasks.add_task(sample_data_task, db)

    return {"message": "抽样任务已启动"}

@router.get("/clear")
async def clear_sample_data(db: Session = Depends(get_db)):
    """清空抽样数据"""
    print("清空抽样数据")
    try:
        db.query(SampleData).delete()
        db.commit()
        return {"message": "抽样数据已清空"}
    except Exception as e:
        db.rollback()
        raise e


@router.delete("/clear-all")
async def clear_all_sample_data(db: Session = Depends(get_db)):    
    try:
        # 使用原生SQL删除所有数据
        db.query(SampleData).delete()
        db.commit()
        return {"message": "所有抽样数据已清空"}
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-year")
async def get_sample_data_stats_by_year(db: Session = Depends(get_db)):
    """按年份统计抽样数据"""
    from sqlalchemy import func

    stats = db.query(
        SampleData.year,
        func.count(SampleData.id).label("count")
    ).group_by(SampleData.year).all()

    return {str(year): count for year, count in stats}

@router.get("/stats/by-task")
async def get_sample_data_stats_by_task(db: Session = Depends(get_db)):
    """按任务统计抽样数据"""
    from sqlalchemy import func
    from app.models.task import Task

    stats = db.query(
        SampleData.task_id,
        Task.task_name,
        func.count(SampleData.id).label("count")
    ).join(Task).group_by(SampleData.task_id, Task.task_name).all()

    return {str(task_id): {"task_name": task_name, "count": count} for task_id, task_name, count in stats}

# 抽样任务
def sample_data_task(db: Session):
    """按配额抽样数据的后台任务"""
    # 获取所有年份配额
    quotas = db.query(YearQuota).all()

    # 按年份范围抽样数据
    for quota in quotas:
        # 获取该年份范围内的所有原始数据
        raw_data_list = db.query(RawData).filter(
            RawData.year >= quota.start_year,
            RawData.year <= quota.end_year
        ).all()

        # 如果原始数据不足，则全部抽取
        if len(raw_data_list) <= quota.sample_num:
            sample_list = raw_data_list
        else:
            # 随机抽样
            sample_list = random.sample(raw_data_list, quota.sample_num)

        # 将抽样数据插入到sample_data表
        for raw_data in sample_list:
            sample_data = SampleData(
                title=raw_data.title,
                content=raw_data.content,
                publish_time=raw_data.publish_time,
                answer_url=raw_data.answer_url,
                author=raw_data.author,
                author_url=raw_data.author_url,
                author_field=raw_data.author_field,
                author_cert=raw_data.author_cert,
                author_fans=raw_data.author_fans,
                year=raw_data.year,
                task_id=raw_data.task_id
            )
            db.add(sample_data)

    db.commit()
