
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.task import Task
from app.models.account import Account
from app.models.crawler_param import CrawlerParam
from pydantic import BaseModel

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])

# Pydantic模型
class TaskBase(BaseModel):
    task_name: str
    account_id: int
    crawler_param_id: Optional[int] = None
    task_type: str  # crawler 或 export

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    account_id: Optional[int] = None
    crawler_param_id: Optional[int] = None
    task_type: Optional[str] = None
    status: Optional[int] = None
    error_message: Optional[str] = None
    progress: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    status: int
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    progress: int

    class Config:
        from_attributes = True

# API路由
@router.get("/", response_model=List[TaskResponse])
async def get_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取任务列表"""
    tasks = db.query(Task).offset(skip).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取单个任务信息"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务ID {task_id} 不存在"
        )
    return task

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """创建新任务"""
    # 检查账号是否存在
    account = db.query(Account).filter(Account.id == task.account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"账号ID {task.account_id} 不存在"
        )

    # 如果提供了小鲸鱼参数ID,检查是否存在
    if task.crawler_param_id:
        crawler_param = db.query(CrawlerParam).filter(CrawlerParam.id == task.crawler_param_id).first()
        if not crawler_param:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"小鲸鱼参数ID {task.crawler_param_id} 不存在"
            )

    # 检查任务类型是否有效
    if task.task_type not in ["crawler", "export"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务类型必须是 crawler 或 export"
        )

    new_task = Task(**task.dict())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """更新任务信息"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务ID {task_id} 不存在"
        )

    # 如果要更新账号ID，检查新账号是否存在
    if task_update.account_id is not None and task_update.account_id != db_task.account_id:
        account = db.query(Account).filter(Account.id == task_update.account_id).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"账号ID {task_update.account_id} 不存在"
            )

    # 如果要更新小鲸鱼参数ID，检查是否存在
    if task_update.crawler_param_id is not None and task_update.crawler_param_id != db_task.crawler_param_id:
        crawler_param = db.query(CrawlerParam).filter(CrawlerParam.id == task_update.crawler_param_id).first()
        if not crawler_param:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"小鲸鱼参数ID {task_update.crawler_param_id} 不存在"
            )

    # 如果要更新任务类型，检查新类型是否有效
    if task_update.task_type and task_update.task_type not in ["crawler", "export"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务类型必须是 crawler 或 export"
        )

    # 更新任务信息
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    # 如果更新了状态，记录时间
    if "status" in update_data:
        if update_data["status"] == 1 and db_task.start_time is None:  # 开始运行
            db_task.start_time = datetime.now()
        elif update_data["status"] in [3, 4, 5]:  # 失败、完成或停止
            db_task.end_time = datetime.now()

    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务ID {task_id} 不存在"
        )

    db.delete(db_task)
    db.commit()
    return None

@router.post("/{task_id}/start", response_model=TaskResponse)
async def start_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """启动任务"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务ID {task_id} 不存在"
        )    

    if db_task.status == 1:  # 已经在运行中
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已在运行中"
        )

    # 更新任务状态为运行中
    db_task.status = 1
    db_task.start_time = datetime.now()
    db.commit()

    # 添加后台任务
    if db_task.task_type == "crawler":
        from app.services.crawler import run_crawler_task
        # 获取爬虫参数
        crawler_params = {}
        if db_task.crawler_param_id:
            from app.models.crawler_param import CrawlerParam
            crawler_param = db.query(CrawlerParam).filter(CrawlerParam.id == db_task.crawler_param_id).first()
            if crawler_param:
                crawler_params = {
                    'url': getattr(crawler_param, 'url', None),
                    'interval': getattr(crawler_param, 'interval', 5),
                    'restart_interval': getattr(crawler_param, 'restart_interval', 3600),
                    'time_range': getattr(crawler_param, 'time_range', (0, 24)),
                    'browser_type': getattr(crawler_param, 'browser_type', 'chromium'),
                    'max_exception': getattr(crawler_param, 'max_exception', 3)
                }
        background_tasks.add_task(run_crawler_task, task_id, **crawler_params)
    elif db_task.task_type == "export":
        from app.services.exporter import run_export_task
        background_tasks.add_task(run_export_task, task_id)

    db.refresh(db_task)
    return db_task

@router.post("/{task_id}/pause", response_model=TaskResponse)
async def pause_task(task_id: int, db: Session = Depends(get_db)):
    """暂停任务"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务ID {task_id} 不存在"
        )

    if db_task.status != 1:  # 不在运行中
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能暂停运行中的任务"
        )

    # 如果是爬虫任务，调用 stop_crawler_task
    if db_task.task_type == "crawler":
        from app.services.crawler import stop_crawler_task
        stop_crawler_task(task_id)

    # 更新任务状态为暂停
    db_task.status = 2
    db.commit()
    db.refresh(db_task)
    return db_task

@router.post("/{task_id}/resume", response_model=TaskResponse)
async def resume_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """恢复任务"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务ID {task_id} 不存在"
        )

    if db_task.status != 2:  # 不在暂停状态
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能恢复暂停的任务"
        )

    # 更新任务状态为运行中
    db_task.status = 1
    db.commit()
    
    # 添加后台任务
    if db_task.task_type == "crawler":        
        from app.services.crawler import run_crawler_task
        background_tasks.add_task(run_crawler_task, task_id)
    elif db_task.task_type == "export":
        from app.services.exporter import run_export_task
        background_tasks.add_task(run_export_task, task_id)

    db.refresh(db_task)
    return db_task

@router.post("/{task_id}/stop", response_model=TaskResponse)
async def stop_task(task_id: int, db: Session = Depends(get_db)):
    """停止任务"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务ID {task_id} 不存在"
        )

    # 如果是爬虫任务，调用 stop_crawler_task
    if db_task.task_type == "crawler":
        from app.services.crawler import stop_crawler_task
        stop_crawler_task(task_id)

    # 更新任务状态为暂停
    db_task.status = 2
    db_task.end_time = datetime.now()
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务ID {task_id} 不存在"
        )

    # 只能删除非运行中的任务
    if db_task.status == 1:  # 运行中
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除运行中的任务，请先停止任务"
        )

    db.delete(db_task)
    db.commit()
    
    return {"message": "任务删除成功"}
