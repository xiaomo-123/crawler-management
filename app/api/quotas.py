
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.year_quota import YearQuota
from pydantic import BaseModel

router = APIRouter(prefix="/api/quotas", tags=["配额管理"])

# Pydantic模型
class QuotaBase(BaseModel):
    start_year: int
    end_year: int
    stock_ratio: float
    sample_num: int

class QuotaCreate(QuotaBase):
    pass

class QuotaUpdate(BaseModel):
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    stock_ratio: Optional[float] = None
    sample_num: Optional[int] = None

class QuotaResponse(QuotaBase):
    id: int

    class Config:
        from_attributes = True

# API路由
@router.get("/", response_model=List[QuotaResponse])
async def get_quotas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取配额列表"""
    quotas = db.query(YearQuota).offset(skip).limit(limit).all()
    return quotas

@router.get("/{quota_id}", response_model=QuotaResponse)
async def get_quota(quota_id: int, db: Session = Depends(get_db)):
    """获取单个配额信息"""
    quota = db.query(YearQuota).filter(YearQuota.id == quota_id).first()
    if not quota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配额ID {quota_id} 不存在"
        )
    return quota

@router.post("/", response_model=QuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_quota(quota: QuotaCreate, db: Session = Depends(get_db)):
    """创建新配额"""
    # 检查年份范围是否合理
    if quota.start_year > quota.end_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始年份不能大于结束年份"
        )

    # 检查存量占比是否在合理范围内
    if quota.stock_ratio < 0 or quota.stock_ratio > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="存量占比必须在0-1之间"
        )

    # 检查抽样条数是否为正数
    if quota.sample_num <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="抽样条数必须为正数"
        )

    new_quota = YearQuota(**quota.model_dump())
    db.add(new_quota)
    db.commit()
    db.refresh(new_quota)
    return new_quota

@router.put("/{quota_id}", response_model=QuotaResponse)
async def update_quota(quota_id: int, quota_update: QuotaUpdate, db: Session = Depends(get_db)):
    """更新配额信息"""
    db_quota = db.query(YearQuota).filter(YearQuota.id == quota_id).first()
    if not db_quota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配额ID {quota_id} 不存在"
        )
    
    # 如果更新了年份范围，检查是否合理
    start_year = quota_update.start_year if quota_update.start_year is not None else db_quota.start_year
    end_year = quota_update.end_year if quota_update.end_year is not None else db_quota.end_year
    
    if start_year > end_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始年份不能大于结束年份"
        )

    # 如果要更新存量占比，检查新值是否在合理范围内
    if quota_update.stock_ratio is not None and (quota_update.stock_ratio < 0 or quota_update.stock_ratio > 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="存量占比必须在0-1之间"
        )

    # 如果要更新抽样条数，检查新值是否为正数
    if quota_update.sample_num is not None and quota_update.sample_num <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="抽样条数必须为正数"
        )

    # 更新配额信息
    update_data = quota_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_quota, key, value)

    db.commit()
    db.refresh(db_quota)
    return db_quota

@router.delete("/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quota(quota_id: int, db: Session = Depends(get_db)):
    """删除配额"""
    db_quota = db.query(YearQuota).filter(YearQuota.id == quota_id).first()
    if not db_quota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配额ID {quota_id} 不存在"
        )

    db.delete(db_quota)
    db.commit()
    return None

@router.post("/init", response_model=List[QuotaResponse])
async def init_quotas(db: Session = Depends(get_db)):
    """初始化配额"""
    # 清空现有配额数据
    db.query(YearQuota).delete()
    db.commit()
    
    # 创建默认配额：开始年份2018，结束年份2025，stock_ratio 0.1，sample_num 1000
    quota = YearQuota(
        start_year=2018,
        end_year=2025,
        stock_ratio=0.1,
        sample_num=1000
    )
    db.add(quota)
    db.commit()
    db.refresh(quota)
    
    return [quota]
