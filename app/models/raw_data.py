
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class RawData(Base):
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
    task = relationship("Task", backref="raw_data")

    # 创建索引
    __table_args__ = (
        Index('idx_year', 'year'),
    )

    def __repr__(self):
        return f"<RawData(id={self.id}, title={self.title[:20]}..., year={self.year}, task_id={self.task_id})>"
