from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from app.database import Base


class CommentData(Base):
    """
    评论数据模型，直接使用comment_data表
    """
    __tablename__ = "comment_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(255), nullable=True, comment="评论作者")
    author_url = Column(String(500), nullable=True, comment="作者链接")
    content = Column(Text, nullable=True, comment="评论内容")
    like_count = Column(Integer, nullable=True, comment="点赞数")
    time = Column(String(20), nullable=True, comment="评论时间")
    raw_data_id = Column(Integer, nullable=False, comment="关联的原始数据ID")
    year = Column(Integer, nullable=False, comment="年份")

    # 创建索引
    __table_args__ = (
        Index('idx_raw_data_id', 'raw_data_id'),
        Index('idx_year', 'year'),
        Index('idx_author', 'author'),
    )

    def __repr__(self):
        return f"<CommentData(id={self.id}, author={self.author}, year={self.year})>"


# 保留CommentDataFactory类以向后兼容，但不再使用分表
class CommentDataFactory:
    """
    已弃用：不再使用分表，直接使用CommentData模型
    """
    @staticmethod
    def get_model(year=None):
        """
        返回CommentData模型，忽略year参数
        """
        return CommentData

    @staticmethod
    def get_all_models():
        """
        返回包含CommentData模型的字典
        """
        return {"default": CommentData}
