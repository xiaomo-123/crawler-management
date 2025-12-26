from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class CrawlerParam(Base):
    """爬虫参数模型"""
    __tablename__ = "crawler_param"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增ID")
    url = Column(String(500), nullable=False, comment="URL地址")
    api_request = Column(String(2000), nullable=False, comment="API请求")
    task_type = Column(String(50), nullable=False, comment="任务类型")
    start_time = Column(DateTime, nullable=True, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    interval_time = Column(Integer, nullable=False, default=1, comment="间隔时间(小时)")
    error_count = Column(Integer, nullable=False, default=3, comment="异常次数")
    restart_browser_time = Column(Integer, nullable=False, default=24, comment="重启浏览器时间(小时)")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<CrawlerParam(id={self.id}, url={self.url}, task_type={self.task_type})>"
