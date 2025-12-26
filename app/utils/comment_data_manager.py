"""
评论数据分表管理工具
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.comment_data import CommentDataFactory, CommentDataBase
from app.database import engine


class CommentDataManager:
    """
    评论数据分表管理类，提供创建表、查询、插入等操作
    注意：comment_data表作为raw_data的分表，根据年月动态创建
    """

    @staticmethod
    def create_table_for_year_month(year: int, month: int) -> bool:
        """
        为指定年月创建评论分表
        """
        try:
            # 获取对应年月的模型
            model = CommentDataFactory.get_model(year, month)

            # 创建表
            model.__table__.create(engine, checkfirst=True)
            return True
        except Exception as e:
            print(f"创建评论表失败: {e}")
            return False

    @staticmethod
    def create_tables_for_year_months(year_months: List[tuple]) -> Dict[str, bool]:
        """
        批量为多个年月创建分表
        year_months: List[(year, month), ...]
        """
        results = {}
        for year, month in year_months:
            key = f"{year}_{month:02d}"
            results[key] = CommentDataManager.create_table_for_year_month(year, month)
        return results

    @staticmethod
    def get_table_names() -> List[str]:
        """
        获取所有评论数据分表的名称
        """
        try:
            with engine.connect() as conn:
                # 检查是否为SQLite数据库
                if "sqlite" in str(engine.url):
                    # SQLite使用sqlite_master系统表
                    result = conn.execute(text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name LIKE 'comment_data_%'"
                    ))
                else:
                    # MySQL使用information_schema系统表
                    result = conn.execute(text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = DATABASE() AND table_name LIKE 'comment_data_%'"
                    ))
                return [row[0] for row in result]
        except Exception as e:
            print(f"获取评论表名失败: {e}")
            return []

    @staticmethod
    def insert_data(data: Dict[str, Any]) -> bool:
        """
        插入数据，自动根据年月选择正确的分表
        """
        try:
            year = data.get('year')
            month = data.get('month')
            if not year or not month:
                raise ValueError("数据中必须包含year和month字段")

            # 确保表存在
            CommentDataManager.create_table_for_year_month(year, month)

            # 获取对应年月的模型
            model = CommentDataFactory.get_model(year, month)

            # 创建并插入数据
            with Session(engine) as session:
                instance = model(**data)
                session.add(instance)
                session.commit()
                return True
        except Exception as e:
            print(f"插入评论数据失败: {e}")
            return False

    @staticmethod
    def batch_insert_data(data_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量插入数据，按年月分组插入到对应分表
        返回每张表插入的记录数
        """
        # 按年月分组数据
        data_by_year_month = {}
        for data in data_list:
            year = data.get('year')
            month = data.get('month')
            if not year or not month:
                continue
            key = f"{year}_{month:02d}"
            if key not in data_by_year_month:
                data_by_year_month[key] = []
            data_by_year_month[key].append(data)

        # 按年月批量插入
        results = {}
        for key, month_data in data_by_year_month.items():
            try:
                year, month = key.split('_')
                year, month = int(year), int(month)

                # 确保表存在
                CommentDataManager.create_table_for_year_month(year, month)

                # 获取对应年月的模型
                model = CommentDataFactory.get_model(year, month)

                # 批量插入
                with Session(engine) as session:
                    instances = [model(**data) for data in month_data]
                    session.bulk_save_objects(instances)
                    session.commit()
                    results[key] = len(month_data)
            except Exception as e:
                print(f"批量插入评论数据失败 (年月: {key}): {e}")
                results[key] = 0

        return results

    @staticmethod
    def query_data(
        years: Optional[List[int]] = None,
        year_months: Optional[List[tuple]] = None,
        author: Optional[str] = None,
        raw_data_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查询数据，可以指定年月、作者、原始数据ID等条件
        """
        try:
            # 确定要查询的年月
            if year_months is None:
                if years is None:
                    # 如果没有指定年月或年份，获取所有分表的年月
                    table_names = CommentDataManager.get_table_names()
                    year_months = []
                    for name in table_names:
                        parts = name.split('_')
                        if len(parts) >= 3:
                            year = int(parts[2])
                            month = int(parts[3])
                            year_months.append((year, month))
                else:
                    # 如果只指定了年份，生成该年份所有月份的年月列表
                    year_months = []
                    for year in years:
                        for month in range(1, 13):
                            year_months.append((year, month))

            # 按年月查询并合并结果
            all_results = []

            for year, month in year_months:
                # 获取对应年月的模型
                model = CommentDataFactory.get_model(year, month)

                # 构建查询
                with Session(engine) as session:
                    query = session.query(model)

                    # 添加过滤条件
                    if author:
                        query = query.filter(model.author == author)
                    if raw_data_id is not None:
                        query = query.filter(model.raw_data_id == raw_data_id)

                    # 分页
                    if offset:
                        query = query.offset(offset)
                    if limit:
                        query = query.limit(limit)

                    # 执行查询
                    results = query.all()
                    all_results.extend([{
                        'id': item.id,
                        'author': item.author,
                        'author_url': item.author_url,
                        'content': item.content,
                        'like_count': item.like_count,
                        'time': item.time,
                        'raw_data_id': item.raw_data_id,
                        'year': item.year,
                        'month': item.month,
                    } for item in results])

            return all_results
        except Exception as e:
            print(f"查询评论数据失败: {e}")
            return []

    @staticmethod
    def get_data_count_by_year() -> Dict[int, int]:
        """
        获取每年分表中的数据量
        """
        try:
            # 获取所有分表的年月
            table_names = CommentDataManager.get_table_names()
            year_months = []
            for name in table_names:
                parts = name.split('_')
                if len(parts) >= 3:
                    year = int(parts[2])
                    month = int(parts[3])
                    year_months.append((year, month))

            # 统计每张表的数据量，并按年份汇总
            results = {}
            for year, month in year_months:
                try:
                    model = CommentDataFactory.get_model(year, month)
                    with Session(engine) as session:
                        count = session.query(model).count()
                        if year in results:
                            results[year] += count
                        else:
                            results[year] = count
                except Exception as e:
                    print(f"统计年月 {year}_{month:02d} 的评论数据量失败: {e}")
                    if year not in results:
                        results[year] = 0

            return results
        except Exception as e:
            print(f"获取评论数据量统计失败: {e}")
            return {}
