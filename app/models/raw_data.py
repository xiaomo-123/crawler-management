
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index, event
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from app.database import Base

class RawData(Base):
    """
    原始数据模型，直接使用raw_data表
    """
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=True, comment="标题")
    content = Column(Text, nullable=True, comment="内容")
    publish_time = Column(String(10), nullable=True, comment="发布时间(YYYY-MM-DD)")
    answer_url = Column(String(500), unique=True, nullable=False, comment="回答链接")
    author = Column(String(255), nullable=True, comment="作者")
    author_url = Column(String(500), nullable=True, comment="作者链接")
    author_field = Column(String(100), nullable=True, comment="作者领域")
    author_cert = Column(String(100), nullable=True, comment="作者认证")
    author_fans = Column(Integer, nullable=True, comment="作者粉丝数")
    year = Column(Integer, nullable=False, comment="年份")
    task_id = Column(Integer, ForeignKey("task.id"), nullable=False, comment="关联任务ID")

    # 关联任务
    task = relationship("Task", lazy='select')

    # 创建索引
    __table_args__ = (
        Index('idx_answer_url', 'answer_url'),
        Index('idx_author', 'author'),
        Index('idx_year', 'year'),
        Index('idx_task_id', 'task_id'),
    )

    def __repr__(self):
        return f"<RawData(id={self.id}, title={self.title[:20]}..., year={self.year}, task_id={self.task_id})>"


# 保留RawDataFactory类以向后兼容，但不再使用分表
class RawDataFactory:
    """
    已弃用：不再使用分表，直接使用RawData模型
    """
    @staticmethod
    def get_model(year=None):
        """
        返回RawData模型，忽略year参数
        """
        return RawData

    @staticmethod
    def get_all_models():
        """
        返回包含RawData模型的字典
        """
        return {"default": RawData}

    @staticmethod
    def find_model_by_id_and_year(data_id, year):
        """
        返回RawData模型，忽略year参数
        """
        return RawData

    @staticmethod
    def find_data_by_id(data_id, db):
        """
        直接从raw_data表查找数据
        返回 (数据, 年份) 元组，如果找不到则返回 (None, None)
        """
        item = db.query(RawData).filter(RawData.id == data_id).first()
        if item:
            return item, item.year
        return None, None
