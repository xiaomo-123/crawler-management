
from sqlalchemy import Column, Integer, String
from app.database import Base

class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_name = Column(String, unique=True, nullable=False, comment="账号cookie内容")
    status = Column(Integer, default=1, nullable=False, comment="状态：1-正常，0-禁用")

    def __repr__(self):
        return f"<Account(id={self.id}, account_name={self.account_name[:10]}..., status={self.status})>"
