"""
评论数据分表管理工具
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.comment_data import CommentDataFactory, CommentData
from app.database import engine


class CommentDataManager:
    """
    评论数据管理类，提供查询、插入等操作
    注意：已不再使用分表，所有操作都针对comment_data表
    """

    @staticmethod
    def create_table() -> bool:
        """
        创建comment_data表
        """
        try:
            # 创建表
            CommentData.__table__.create(engine, checkfirst=True)
            return True
        except Exception as e:
            print(f"创建评论表失败: {e}")
            return False

    @staticmethod
    def get_table_names() -> List[str]:
        """
        获取评论数据表的名称
        """
        try:
            with engine.connect() as conn:
                # 查询comment_data表
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = DATABASE() AND table_name = 'comment_data'"
                ))
                return [row[0] for row in result]
        except Exception as e:
            print(f"获取评论表名失败: {e}")
            return []

    @staticmethod
    def insert_data(data: Dict[str, Any]) -> bool:
        """
        插入数据到comment_data表
        """
        try:
            year = data.get('year')
            if not year:
                raise ValueError("数据中必须包含year字段")

            # 确保表存在
            CommentDataManager.create_table()

            # 创建并插入数据
            with Session(engine) as session:
                instance = CommentData(**data)
                session.add(instance)
                session.commit()
                return True
        except Exception as e:
            print(f"插入评论数据失败: {e}")
            return False

    @staticmethod
    def batch_insert_data(data_list: List[Dict[str, Any]]) -> int:
        """
        批量插入数据到comment_data表
        返回插入的记录数
        """
        try:
            # 确保表存在
            CommentDataManager.create_table()

            # 批量插入
            with Session(engine) as session:
                instances = [CommentData(**data) for data in data_list]
                session.bulk_save_objects(instances)
                session.commit()
                return len(data_list)
        except Exception as e:
            print(f"批量插入评论数据失败: {e}")
            return 0

    @staticmethod
    def query_data(
        years: Optional[List[int]] = None,
        author: Optional[str] = None,
        raw_data_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查询数据，可以指定年份、作者、原始数据ID等条件
        """
        try:
            # 构建查询
            with Session(engine) as session:
                query = session.query(CommentData)

                # 添加过滤条件
                if author:
                    query = query.filter(CommentData.author == author)
                if raw_data_id is not None:
                    query = query.filter(CommentData.raw_data_id == raw_data_id)
                if years is not None and len(years) > 0:
                    query = query.filter(CommentData.year.in_(years))

                # 分页
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)

                # 执行查询
                results = query.all()
                return [{
                    'id': item.id,
                    'author': item.author,
                    'author_url': item.author_url,
                    'content': item.content,
                    'like_count': item.like_count,
                    'time': item.time,
                    'raw_data_id': item.raw_data_id,
                    'year': item.year,
                } for item in results]
        except Exception as e:
            print(f"查询评论数据失败: {e}")
            return []

    @staticmethod
    def get_data_count_by_year() -> Dict[int, int]:
        """
        获取每年的评论数据量
        """
        try:
            # 统计每年的数据量
            with Session(engine) as session:
                # 使用SQL按年份分组统计
                result = session.execute(text(
                    "SELECT year, COUNT(*) as count FROM comment_data GROUP BY year"
                ))
                return {row[0]: row[1] for row in result}
        except Exception as e:
            print(f"获取评论数据量统计失败: {e}")
            return {}
