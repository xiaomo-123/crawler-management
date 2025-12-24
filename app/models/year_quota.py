
from sqlalchemy import Column, Integer, Float
from app.database import Base

class YearQuota(Base):
    __tablename__ = "year_quota"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_year = Column(Integer, nullable=False, comment="开始年份")
    end_year = Column(Integer, nullable=False, comment="结束年份")
    stock_ratio = Column(Float, nullable=False, comment="存量占比")
    sample_num = Column(Integer, nullable=False, comment="抽样条数")

    def __repr__(self):
        return f"<YearQuota(start_year={self.start_year}, end_year={self.end_year}, ratio={self.stock_ratio}, num={self.sample_num})>"
