
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import random
from app.database import get_db
from app.models.raw_data import RawData
from app.models.comment_data import CommentData
from app.models.task import Task
from app.utils.raw_data_manager import RawDataManager
from pydantic import BaseModel

router = APIRouter(prefix="/api/raw-data", tags=["raw-data"])

def get_random_task_id(db: Session) -> int:
    """获取随机任务ID"""
    # 获取所有任务ID
    task_ids = db.query(Task.id).all()
    if not task_ids:
        # 如果没有任务，返回1
        return 1
    # 随机选择一个任务ID
    return random.choice(task_ids)[0]

# 评论数据Pydantic模型
class CommentDataBase(BaseModel):
    author: Optional[str] = None
    author_url: Optional[str] = None
    content: Optional[str] = None
    like_count: Optional[int] = None
    time: Optional[str] = None

class CommentDataResponse(CommentDataBase):
    id: int
    raw_data_id: int
    year: int

    class Config:
        from_attributes = True

# 原始数据Pydantic模型
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
    comments_structured: Optional[List[Dict[str, Any]]] = None  # 新增评论结构化数据字段

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
    comments_structured: Optional[List[Dict[str, Any]]] = None

class RawDataResponse(RawDataBase):
    id: int

    class Config:
        from_attributes = True

class DeleteAllResponse(BaseModel):
    deleted_count: int

class EmptyRequest(BaseModel):
    pass

# API路由
@router.get("/", response_model=List[RawDataResponse])
async def get_raw_data(skip: int = 0, limit: int = 100, year: Optional[int] = None, task_id: Optional[int] = None, db: Session = Depends(get_db)):
    """获取原始数据列表"""
    # 直接从raw_data表查询
    query = db.query(RawData)

    # 添加过滤条件
    if year is not None:
        query = query.filter(RawData.year == year)
    if task_id is not None:
        query = query.filter(RawData.task_id == task_id)

    # 分页
    query = query.offset(skip).limit(limit)

    # 执行查询
    raw_data = query.all()

    # 转换为响应模型
    response_data = []
    for item in raw_data:
        response_data.append(RawDataResponse(
            id=item.id,
            title=item.title,
            content=item.content,
            publish_time=item.publish_time,
            answer_url=item.answer_url,
            author=item.author,
            author_url=item.author_url,
            author_field=item.author_field,
            author_cert=item.author_cert,
            author_fans=item.author_fans,
            year=item.year,
            task_id=item.task_id
        ))

    return response_data

@router.get("/{data_id}", response_model=RawDataResponse)
async def get_raw_data_item(data_id: int, db: Session = Depends(get_db)):
    """获取单个原始数据"""
    # 直接从raw_data表查询
    data = db.query(RawData).filter(RawData.id == data_id).first()
    data_year = data.year if data else None

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"原始数据ID {data_id} 不存在"
        )

    # 转换为响应模型
    return RawDataResponse(
        id=data.id,
        title=data.title,
        content=data.content,
        publish_time=data.publish_time,
        answer_url=data.answer_url,
        author=data.author,
        author_url=data.author_url,
        author_field=data.author_field,
        author_cert=data.author_cert,
        author_fans=data.author_fans,
        year=data.year,
        task_id=data.task_id
    )

@router.post("/", response_model=RawDataResponse, status_code=status.HTTP_201_CREATED)
async def create_raw_data(raw_data: RawDataCreate, db: Session = Depends(get_db)):
    """创建新原始数据"""
    # 检查任务是否存在
    from app.models.task import Task
    task = db.query(Task).filter(Task.id == raw_data.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务ID {raw_data.task_id} 不存在"
        )

    # 检查answer_url是否已存在
    existing_data = db.query(RawData).filter(RawData.answer_url == raw_data.answer_url).first()
    if existing_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="回答链接已存在"
        )

    # 准备数据
    data_dict = raw_data.model_dump()

    # 分离评论数据
    comments = data_dict.pop('comments_structured', None)

    # 创建原始数据对象
    new_raw_data = RawData(**data_dict)
    db.add(new_raw_data)
    db.commit()
    db.refresh(new_raw_data)  # 获取数据库生成的ID

    # 如果有评论数据，插入评论分表
    if comments and len(comments) > 0:
        # 从原始数据的publish_time字段提取年月
        publish_time = raw_data.publish_time
        if publish_time:
            # publish_time是字符串格式，使用"-"符号分割
            if isinstance(publish_time, str):
                parts = publish_time.split('-')
                if len(parts) >= 2:
                    year = int(parts[0])
                    month = int(parts[1])
                else:
                    # 如果格式不正确，使用year字段
                    year = raw_data.year
                    month = 1  # 默认为1月
            else:
                # 如果不是字符串，使用year字段
                year = raw_data.year
                month = 1  # 默认为1月
        else:
            # 如果没有publish_time，使用year字段
            year = raw_data.year
            month = 1  # 默认为1月

        # 获取对应年月的评论分表模型
        from app.models.comment_data import CommentDataFactory
        comment_model = CommentDataFactory.get_model(year, month)

        # 确保分表存在
        from app.utils.comment_data_manager import CommentDataManager
        CommentDataManager.create_table_for_year_month(year, month)

        for comment in comments:
            comment_data = comment_model(
                author=comment.get('author'),
                author_url=comment.get('author_url'),
                content=comment.get('content'),
                like_count=comment.get('like_count'),
                time=comment.get('time'),
                raw_data_id=new_raw_data.id,
                year=year,
                month=month
            )
            db.add(comment_data)

        db.commit()  # 提交所有评论数据

    # 返回新创建的数据
    return RawDataResponse(
        id=new_raw_data.id,
        title=new_raw_data.title,
        content=new_raw_data.content,
        publish_time=new_raw_data.publish_time,
        answer_url=new_raw_data.answer_url,
        author=new_raw_data.author,
        author_url=new_raw_data.author_url,
        author_field=new_raw_data.author_field,
        author_cert=new_raw_data.author_cert,
        author_fans=new_raw_data.author_fans,
        year=new_raw_data.year,
        task_id=new_raw_data.task_id
    )

@router.put("/{data_id}", response_model=RawDataResponse)
async def update_raw_data(data_id: int, data_update: RawDataUpdate, db: Session = Depends(get_db)):
    """更新原始数据"""
    # 直接从raw_data表查询
    db_data = db.query(RawData).filter(RawData.id == data_id).first()

    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"原始数据ID {data_id} 不存在"
        )

    # 更新数据信息
    update_data = data_update.model_dump(exclude_unset=True)

    # 处理评论数据
    comments = update_data.pop('comments_structured', None)

    # 更新原始数据
    for key, value in update_data.items():
        setattr(db_data, key, value)

    db.commit()

    # 如果有评论数据，更新评论分表
    if comments is not None:
        # 从原始数据的publish_time字段提取年月
        publish_time = db_data.publish_time
        if publish_time:
            # publish_time是字符串格式，使用"-"符号分割
            if isinstance(publish_time, str):
                parts = publish_time.split('-')
                if len(parts) >= 2:
                    year = int(parts[0])
                    month = int(parts[1])
                else:
                    # 如果格式不正确，使用year字段
                    year = db_data.year
                    month = 1  # 默认为1月
            else:
                # 如果不是字符串，使用year字段
                year = db_data.year
                month = 1  # 默认为1月
        else:
            # 如果没有publish_time，使用year字段
            year = db_data.year
            month = 1  # 默认为1月

        # 先删除原有评论
        from app.models.comment_data import CommentDataFactory
        comment_model = CommentDataFactory.get_model(year, month)
        old_comments = db.query(comment_model).filter(comment_model.raw_data_id == data_id).all()
        for comment in old_comments:
            db.delete(comment)

        if comments and len(comments) > 0:
            comment_data_list = []
            for comment in comments:
                comment_data = {
                    'author': comment.get('author'),
                    'author_url': comment.get('author_url'),
                    'content': comment.get('content'),
                    'like_count': comment.get('like_count'),
                    'time': comment.get('time'),
                    'raw_data_id': data_id,
                    'year': year,
                    'month': month
                }
                comment_data_list.append(comment_data)

            # 批量插入评论数据
            from app.utils.comment_data_manager import CommentDataManager
            CommentDataManager.batch_insert_data(comment_data_list)

    db.refresh(db_data)

    # 转换为响应模型
    return RawDataResponse(
        id=db_data.id,
        title=db_data.title,
        content=db_data.content,
        publish_time=db_data.publish_time,
        answer_url=db_data.answer_url,
        author=db_data.author,
        author_url=db_data.author_url,
        author_field=db_data.author_field,
        author_cert=db_data.author_cert,
        author_fans=db_data.author_fans,
        year=db_data.year,
        task_id=db_data.task_id
    )



@router.delete("/clear-all")
async def clear_all_raw_data(request: EmptyRequest = None, db: Session = Depends(get_db)):
    """删除所有原始数据"""
    try:
        # 直接从raw_data表删除所有数据
        deleted_raw_data = db.query(RawData).delete()

        # 删除所有评论分表中的数据
        from app.utils.comment_data_manager import CommentDataManager
        table_names = CommentDataManager.get_table_names()
        total_deleted_comment_data = 0

        for table_name in table_names:
            # 从表名提取年月
            parts = table_name.split('_')
            if len(parts) >= 3:
                year = int(parts[2])
                month = int(parts[3])

                # 获取对应年月的评论分表模型
                from app.models.comment_data import CommentDataFactory
                comment_model = CommentDataFactory.get_model(year, month)

                # 删除分表中的所有数据
                deleted = db.query(comment_model).delete()
                total_deleted_comment_data += deleted

        db.commit()
        return {"message": f"所有原始数据已删除，共删除 {deleted_raw_data} 条原始数据和 {total_deleted_comment_data} 条评论"}
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_raw_data(data_id: int, db: Session = Depends(get_db)):
    """删除原始数据"""
    # 直接从raw_data表查询
    db_data = db.query(RawData).filter(RawData.id == data_id).first()

    if not db_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"原始数据ID {data_id} 不存在"
        )

    # 删除相关评论
    # 从原始数据的publish_time字段提取年月
    publish_time = db_data.publish_time
    if publish_time:
        # publish_time是字符串格式，使用"-"符号分割
        if isinstance(publish_time, str):
            parts = publish_time.split('-')
            if len(parts) >= 2:
                year = int(parts[0])
                month = int(parts[1])
            else:
                # 如果格式不正确，使用year字段
                year = db_data.year
                month = 1  # 默认为1月
        else:
            # 如果不是字符串，使用year字段
            year = db_data.year
            month = 1  # 默认为1月
    else:
        # 如果没有publish_time，使用year字段
        year = db_data.year
        month = 1  # 默认为1月

    # 根据年月获取对应的评论分表模型
    from app.models.comment_data import CommentDataFactory
    comment_model = CommentDataFactory.get_model(year, month)

    # 从对应年月的评论分表删除评论
    comment_data = db.query(comment_model).filter(comment_model.raw_data_id == data_id).all()
    for comment in comment_data:
        db.delete(comment)

    # 删除原始数据
    db.delete(db_data)
    db.commit()
    return None

@router.get("/delete-all")
async def delete_all_raw_data(db: Session = Depends(get_db)):
    """删除所有原始数据"""
    print("Deleting all raw data...")    
    try:
        # 使用RawDataManager删除所有数据
        from app.models.raw_data import RawDataFactory
        table_names = RawDataManager.get_table_names()
        years = [int(name.split('_')[-1]) for name in table_names]

        total_deleted = 0
        for year in years:
            model = RawDataFactory.get_model(year)
            deleted = db.query(model).delete()
            total_deleted += deleted

        db.commit()
        return {"message": f"所有原始数据已删除，共删除 {total_deleted} 条记录"}
    except Exception as e:
        db.rollback()
        raise e


@router.delete("/clear-all")
async def clear_all_raw_data(request: EmptyRequest = None, db: Session = Depends(get_db)):  
    
    try:
        # 使用RawDataManager删除所有数据
        from app.models.raw_data import RawDataFactory
        table_names = RawDataManager.get_table_names()
        years = [int(name.split('_')[-1]) for name in table_names]

        total_deleted = 0
        for year in years:
            model = RawDataFactory.get_model(year)
            deleted = db.query(model).delete()
            total_deleted += deleted

        db.commit()
        return {"message": f"所有原始数据已删除，共删除 {total_deleted} 条记录"}
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-year")
async def get_raw_data_stats_by_year(db: Session = Depends(get_db)):
    """按年份统计原始数据"""
    # 直接从raw_data表按年份统计数据
    from sqlalchemy import func
    stats = db.query(
        RawData.year,
        func.count(RawData.id).label('count')
    ).group_by(RawData.year).all()

    return {str(year): count for year, count in stats}

@router.get("/stats/by-task")
async def get_raw_data_stats_by_task(db: Session = Depends(get_db)):
    """按任务统计原始数据"""
    # 获取所有任务ID
    from app.models.task import Task
    tasks = db.query(Task).all()

    # 统计每个任务的数据量
    stats = {}
    for task in tasks:
        # 直接从raw_data表查询该任务的所有数据
        task_data_count = db.query(RawData).filter(RawData.task_id == task.id).count()
        stats[str(task.id)] = {
            "task_name": task.task_name,
            "count": task_data_count
        }

    return stats

# 新增获取评论数据的路由
@router.get("/{data_id}/comments", response_model=List[CommentDataResponse])
async def get_raw_data_comments(data_id: int, db: Session = Depends(get_db)):
    """获取原始数据的评论"""
    # 先从raw_data主表查询
    data = db.query(RawData).filter(RawData.id == data_id).first()

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"原始数据ID {data_id} 不存在"
        )

    # 从原始数据的publish_time字段提取年月
    publish_time = data.publish_time
    if publish_time:
        # publish_time是字符串格式，使用"-"符号分割
        if isinstance(publish_time, str):
            parts = publish_time.split('-')
            if len(parts) >= 2:
                year = int(parts[0])
                month = int(parts[1])
            else:
                # 如果格式不正确，使用year字段
                year = data.year
                month = 1  # 默认为1月
        else:
            # 如果不是字符串，使用year字段
            year = data.year
            month = 1  # 默认为1月
    else:
        # 如果没有publish_time，使用year字段
        year = data.year
        month = 1  # 默认为1月

    # 根据年月获取对应的评论分表模型
    from app.models.comment_data import CommentDataFactory
    comment_model = CommentDataFactory.get_model(year, month)

    # 从对应年月的评论分表查询评论
    comments = db.query(comment_model).filter(comment_model.raw_data_id == data_id).all()

    # 转换为响应模型
    response_data = []
    for comment in comments:
        response_data.append(CommentDataResponse(
            id=comment.id,
            author=comment.author,
            author_url=comment.author_url,
            content=comment.content,
            like_count=comment.like_count,
            time=comment.time,
            raw_data_id=comment.raw_data_id,
            year=comment.year
        ))

    return response_data

# 新增导入JSON数据的API端点
@router.post("/import-json", status_code=status.HTTP_201_CREATED)
async def import_json_data(
    db: Session = Depends(get_db),
    json_data: List[Dict[str, Any]] = Body(...)
):
    """导入JSON格式的原始数据"""    
    if not json_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有提供JSON数据"
        )

    try:
        success_count = 0
        error_count = 0
        errors = []

        for idx, item in enumerate(json_data):
            try:
                # 检查必填字段
                if 'url' not in item:
                    errors.append(f"第{idx+1}条数据缺少url字段")
                    error_count += 1
                    continue

                # 检查answer_url是否已存在
                answer_url = item['url']
                existing_data = db.query(RawData).filter(RawData.answer_url == answer_url).first()
                if existing_data:
                    errors.append(f"第{idx+1}条数据的URL已存在")
                    error_count += 1
                    continue

                # 准备数据
                data_dict = {
                    'title': item.get('title', ''),
                    'content': item.get('content', ''),
                    'answer_url': answer_url,
                    'author': item.get('author', ''),
                    'author_url': item.get('author_url', ''),
                    'author_field': item.get('author_field', ''),
                    'author_cert': item.get('author_cert', ''),
                    'author_fans': item.get('author_fans', 0),
                    'year': item.get('year', 2023),  # 默认年份
                    'task_id': get_random_task_id(db),  # 随机任务ID
                    'publish_time': item.get('publish_time', '')
                }

                # 分离评论数据
                comments = item.get('comments_structured', [])

                # 创建原始数据对象
                new_raw_data = RawData(**data_dict)
                db.add(new_raw_data)
                db.commit()
                db.refresh(new_raw_data)  # 获取数据库生成的ID

                # 如果有评论数据，插入评论分表
                if comments and len(comments) > 0:
                    # 从原始数据的publish_time字段提取年月
                    publish_time = data_dict.get('publish_time', '')
                    if publish_time:
                        # publish_time是字符串格式，使用"-"符号分割
                        if isinstance(publish_time, str):
                            parts = publish_time.split('-')
                            if len(parts) >= 2:
                                year = int(parts[0])
                                month = int(parts[1])
                            else:
                                # 如果格式不正确，使用year字段
                                year = data_dict.get('year', 2023)
                                month = 1  # 默认为1月
                        else:
                            # 如果不是字符串，使用year字段
                            year = data_dict.get('year', 2023)
                            month = 1  # 默认为1月
                    else:
                        # 如果没有publish_time，使用year字段
                        year = data_dict.get('year', 2023)
                        month = 1  # 默认为1月

                    # 获取对应年月的评论分表模型
                    from app.models.comment_data import CommentDataFactory
                    comment_model = CommentDataFactory.get_model(year, month)

                    # 确保分表存在
                    from app.utils.comment_data_manager import CommentDataManager
                    CommentDataManager.create_table_for_year_month(year, month)

                    for comment in comments:
                        comment_data = comment_model(
                            author=comment.get('author', ''),
                            author_url=comment.get('author_url', ''),
                            content=comment.get('content', ''),
                            like_count=comment.get('like_count', 0),
                            time=comment.get('time', ''),
                            raw_data_id=new_raw_data.id,
                            year=year,
                            month=month
                        )
                        db.add(comment_data)

                    db.commit()  # 提交所有评论数据

                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"第{idx+1}条数据处理失败: {str(e)}")
                db.rollback()
                continue

        return {
            "message": f"JSON数据导入完成，成功导入 {success_count} 条，失败 {error_count} 条",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入JSON数据时发生错误: {str(e)}"
        )

