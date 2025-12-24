"""
原始数据分表管理工具
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.raw_data import RawDataFactory, RawData
from app.database import engine


class RawDataManager:
    """
    原始数据管理类，提供查询、插入等操作
    注意：已不再使用分表，所有操作都针对raw_data表
    """

    @staticmethod
    def create_table() -> bool:
        """
        创建raw_data表
        """
        try:
            # 创建表
            RawData.__table__.create(engine, checkfirst=True)
            return True
        except Exception as e:
            print(f"创建表失败: {e}")
            return False

    @staticmethod
    def get_table_names() -> List[str]:
        """
        获取原始数据表的名称
        """
        try:
            with engine.connect() as conn:
                # 查询raw_data表
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = DATABASE() AND table_name = 'raw_data'"
                ))
                return [row[0] for row in result]
        except Exception as e:
            print(f"获取表名失败: {e}")
            return []

    @staticmethod
    def insert_data(data: Dict[str, Any]) -> bool:
        """
        插入数据到raw_data表
        """
        try:
            year = data.get('year')
            if not year:
                raise ValueError("数据中必须包含year字段")

            # 确保表存在
            RawDataManager.create_table()

            # 创建并插入数据
            with Session(engine) as session:
                instance = RawData(**data)
                session.add(instance)
                session.commit()
                return True
        except Exception as e:
            print(f"插入数据失败: {e}")
            return False

    @staticmethod
    def batch_insert_data(data_list: List[Dict[str, Any]]) -> int:
        """
        批量插入数据到raw_data表
        返回插入的记录数
        """
        try:
            # 确保表存在
            RawDataManager.create_table()

            # 批量插入
            with Session(engine) as session:
                instances = [RawData(**data) for data in data_list]
                session.bulk_save_objects(instances)
                session.commit()
                return len(data_list)
        except Exception as e:
            print(f"批量插入数据失败: {e}")
            return 0

    @staticmethod
    def query_data(
        years: Optional[List[int]] = None,
        author: Optional[str] = None,
        task_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查询数据，可以指定年份、作者、任务ID等条件
        """
        try:
            # 构建查询
            with Session(engine) as session:
                query = session.query(RawData)

                # 添加过滤条件
                if author:
                    query = query.filter(RawData.author == author)
                if task_id is not None:
                    query = query.filter(RawData.task_id == task_id)
                if years is not None and len(years) > 0:
                    query = query.filter(RawData.year.in_(years))

                # 分页
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)

                # 执行查询
                results = query.all()
                return [{
                    'id': item.id,
                    'title': item.title,
                    'content': item.content,
                    'publish_time': item.publish_time,
                    'answer_url': item.answer_url,
                    'author': item.author,
                    'author_url': item.author_url,
                    'author_field': item.author_field,
                    'author_cert': item.author_cert,
                    'author_fans': item.author_fans,
                    'year': item.year,
                    'task_id': item.task_id,
                } for item in results]
        except Exception as e:
            print(f"查询数据失败: {e}")
            return []

    @staticmethod
    def get_data_count_by_year() -> Dict[int, int]:
        """
        获取每年的数据量
        """
        try:
            # 统计每年的数据量
            with Session(engine) as session:
                # 使用SQL按年份分组统计
                result = session.execute(text(
                    "SELECT year, COUNT(*) as count FROM raw_data GROUP BY year"
                ))
                return {row[0]: row[1] for row in result}
        except Exception as e:
            print(f"获取数据量统计失败: {e}")
            return {}
