
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from app.database import Base

class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(255), nullable=False, comment="任务名称")
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False, comment="关联账号ID")
    crawler_param_id = Column(Integer, ForeignKey("crawler_param.id"), nullable=True, comment="关联小鲸鱼参数ID")
    task_type = Column(String(50), nullable=False, comment="任务类型：crawler-小鲸鱼，export-Excel生成")
    status = Column(Integer, default=0, nullable=False, comment="状态：0-等待，1-运行，2-暂停，3-失败，4-完成")
    start_time = Column(DateTime, default=datetime.now, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    error_message = Column(Text, nullable=True, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")
    progress = Column(Integer, default=0, comment="进度百分比")

    # 关联账号
    account = relationship("Account", backref="tasks")
    # 关联小鲸鱼参数
    crawler_param = relationship("CrawlerParam", backref="tasks")

    # 使用@declared_attr创建动态关系，避免与RawData模型冲突
    @declared_attr
    def raw_data_list(cls):
        # 由于RawData是分表模型，我们不能直接创建关系
        # 这里只返回None，实际查询需要使用RawDataManager
        return None

    def __repr__(self):
        return f"<Task(id={self.id}, name={self.task_name}, type={self.task_type}, status={self.status})>"
