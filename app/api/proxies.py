
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.proxy import Proxy
from pydantic import BaseModel

router = APIRouter(prefix="/api/proxies", tags=["代理管理"])

# Pydantic模型
class ProxyBase(BaseModel):
    proxy_type: str
    proxy_addr: str
    status: int = 1
    strategy: str = "轮询"

class ProxyCreate(ProxyBase):
    pass

class ProxyUpdate(BaseModel):
    proxy_type: Optional[str] = None
    proxy_addr: Optional[str] = None
    status: Optional[int] = None
    strategy: Optional[str] = None

class ProxyResponse(ProxyBase):
    id: int

    class Config:
        from_attributes = True

# API路由
@router.get("/", response_model=List[ProxyResponse])
async def get_proxies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取代理列表"""
    proxies = db.query(Proxy).offset(skip).limit(limit).all()
    return proxies

@router.get("/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(proxy_id: int, db: Session = Depends(get_db)):
    """获取单个代理信息"""
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"代理ID {proxy_id} 不存在"
        )
    return proxy

@router.post("/", response_model=ProxyResponse, status_code=status.HTTP_201_CREATED)
async def create_proxy(proxy: ProxyCreate, db: Session = Depends(get_db)):
    """创建新代理"""
    # 检查代理地址是否已存在
    db_proxy = db.query(Proxy).filter(Proxy.proxy_addr == proxy.proxy_addr).first()
    if db_proxy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="代理地址已存在"
        )

    # 检查代理类型是否有效
    if proxy.proxy_type not in ["HTTP", "HTTPS", "SOCKS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="代理类型必须是 HTTP、HTTPS 或 SOCKS"
        )

    # 检查策略是否有效
    if proxy.strategy not in ["轮询", "随机", "失败切换"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="策略必须是 轮询、随机 或 失败切换"
        )

    new_proxy = Proxy(**proxy.model_dump())
    db.add(new_proxy)
    db.commit()
    db.refresh(new_proxy)
    return new_proxy

@router.put("/{proxy_id}", response_model=ProxyResponse)
async def update_proxy(proxy_id: int, proxy_update: ProxyUpdate, db: Session = Depends(get_db)):
    """更新代理信息"""
    db_proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not db_proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"代理ID {proxy_id} 不存在"
        )

    # 如果要更新代理地址，检查新代理地址是否已存在
    if proxy_update.proxy_addr and proxy_update.proxy_addr != db_proxy.proxy_addr:
        existing_proxy = db.query(Proxy).filter(Proxy.proxy_addr == proxy_update.proxy_addr).first()
        if existing_proxy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="代理地址已存在"
            )

    # 如果要更新代理类型，检查新类型是否有效
    if proxy_update.proxy_type and proxy_update.proxy_type not in ["HTTP", "HTTPS", "SOCKS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="代理类型必须是 HTTP、HTTPS 或 SOCKS"
        )

    # 如果要更新策略，检查新策略是否有效
    if proxy_update.strategy and proxy_update.strategy not in ["轮询", "随机", "失败切换"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="策略必须是 轮询、随机 或 失败切换"
        )

    # 更新代理信息
    update_data = proxy_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_proxy, key, value)

    db.commit()
    db.refresh(db_proxy)
    return db_proxy

@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy(proxy_id: int, db: Session = Depends(get_db)):
    """删除代理"""
    db_proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not db_proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"代理ID {proxy_id} 不存在"
        )

    db.delete(db_proxy)
    db.commit()
    return None

@router.get("/random/available", response_model=ProxyResponse)
async def get_random_available_proxy(db: Session = Depends(get_db)):
    """获取随机可用代理"""
    import random

    # 获取所有可用代理
    available_proxies = db.query(Proxy).filter(Proxy.status == 1).all()
    if not available_proxies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有可用的代理"
        )

    # 随机选择一个代理
    proxy = random.choice(available_proxies)
    return proxy

@router.delete("/{proxy_id}")
async def delete_proxy(proxy_id: int, db: Session = Depends(get_db)):
    """删除代理"""
    db_proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not db_proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"代理ID {proxy_id} 不存在"
        )

    db.delete(db_proxy)
    db.commit()
    
    return {"message": "代理删除成功"}
