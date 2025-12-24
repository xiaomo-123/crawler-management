from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from app.database import Base


class CommentDataBase(Base):
    """
    评论数据基类，包含所有分表的共同字段和方法
    """
    __abstract__ = True  # 抽象类，不会创建表

    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(255), nullable=True, comment="评论作者")
    author_url = Column(String(500), nullable=True, comment="作者链接")
    content = Column(Text, nullable=True, comment="评论内容")
    like_count = Column(Integer, nullable=True, comment="点赞数")
    time = Column(String(20), nullable=True, comment="评论时间")
    raw_data_id = Column(Integer, nullable=False, comment="关联的原始数据ID")
    year = Column(Integer, nullable=False, comment="年份")
    month = Column(Integer, nullable=False, comment="月份")

    # 使用@declared_attr确保每个子表都有自己独立的索引
    @declared_attr
    def __table_args__(cls):
        return (
            Index(f'idx_raw_data_id_{cls.__tablename__}', 'raw_data_id'),
            Index(f'idx_year_month_{cls.__tablename__}', 'year', 'month'),
            Index(f'idx_author_{cls.__tablename__}', 'author'),
        )

    def __repr__(self):
        return f"<CommentData(id={self.id}, author={self.author}, year={self.year}, month={self.month})>"


class CommentDataFactory:
    """
    动态创建按年月分表的CommentData模型
    """
    _models = {}

    @classmethod
    def get_model(cls, year, month):
        """
        获取指定年月的CommentData模型，如果不存在则创建
        """
        key = f"{year}_{month}"
        if key in cls._models:
            return cls._models[key]

        # 动态创建模型类
        class_name = f"CommentData{year}{month:02d}"
        table_name = f"comment_data_{year}_{month:02d}"

        # 创建新类，继承自CommentDataBase
        model = type(
            class_name,
            (CommentDataBase,),
            {
                "__tablename__": table_name,
            }
        )

        # 缓存模型
        cls._models[key] = model
        return model

    @classmethod
    def get_all_models(cls):
        """
        获取所有已创建的模型
        """
        return cls._models

    @classmethod
    def get_model_by_raw_data(cls, db, raw_data_id):
        """
        根据原始数据ID获取对应的评论分表模型
        """
        # 先从raw_data表查询该记录的年月信息
        from app.models.raw_data import RawData
        raw_data = db.query(RawData).filter(RawData.id == raw_data_id).first()
        if not raw_data:
            raise ValueError(f"原始数据ID {raw_data_id} 不存在")

        # 从原始数据的publish_time字段提取年月
        publish_time = raw_data.publish_time
        if not publish_time:
            # 如果没有publish_time，使用year字段
            year = raw_data.year
            month = 1  # 默认为1月
        else:
            # 从publish_time提取年月
            year = publish_time.year
            month = publish_time.month

        return cls.get_model(year, month)


class CommentData(CommentDataBase):
    """
    默认CommentData模型，用于向后兼容和通用操作
    实际数据会存储在按年月分表中
    """
    __tablename__ = "comment_data"  # 保留原始表名作为主表

    # 当插入数据时，根据年月自动选择正确的分表
    @classmethod
    def create_instance(cls, **kwargs):
        """
        创建CommentData实例，自动根据年月选择正确的分表模型
        """
        year = kwargs.get('year')
        month = kwargs.get('month')
        if not year or not month:
            raise ValueError("必须提供year和month参数")

        # 获取对应年月的模型
        model = CommentDataFactory.get_model(year, month)

        # 创建实例
        return model(**kwargs)
