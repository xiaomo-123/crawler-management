
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(255), nullable=False, comment="任务名称")
    account_name = Column(String, ForeignKey("account.account_name"), nullable=False, comment="关联账号")
    task_type = Column(String(50), nullable=False, comment="任务类型：crawler-爬虫，export-Excel生成")
    status = Column(Integer, default=0, nullable=False, comment="状态：0-等待，1-运行，2-暂停，3-失败，4-完成")
    start_time = Column(DateTime, default=datetime.now, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    error_message = Column(Text, nullable=True, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")
    progress = Column(Integer, default=0, comment="进度百分比")

    # 关联账号
    account = relationship("Account", backref="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, name={self.task_name}, type={self.task_type}, status={self.status})>"
