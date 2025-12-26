
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.account import Account
from pydantic import BaseModel

router = APIRouter(prefix="/api/accounts", tags=["账号管理"])

# Pydantic模型
class AccountBase(BaseModel):
    account_name: str
    status: int = 1

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    status: Optional[int] = None

class AccountResponse(AccountBase):
    id: int

    class Config:
        from_attributes = True

# API路由
@router.get("/", response_model=List[AccountResponse])
async def get_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取账号列表"""
    accounts = db.query(Account).offset(skip).limit(limit).all()
    return accounts

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """获取单个账号信息"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"账号ID {account_id} 不存在"
        )
    return account

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """创建新账号"""
    new_account = Account(**account.model_dump())
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: int, account_update: AccountUpdate, db: Session = Depends(get_db)):
    """更新账号信息"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"账号ID {account_id} 不存在"
        )

    # 如果要更新账号名，检查新账号名是否已存在
    if account_update.account_name and account_update.account_name != db_account.account_name:
        existing_account = db.query(Account).filter(Account.account_name == account_update.account_name).first()
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账号名已存在"
            )

    # 更新账号信息
    update_data = account_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_account, key, value)

    db.commit()
    db.refresh(db_account)
    return db_account

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """删除账号"""
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"账号ID {account_id} 不存在"
        )

    db.delete(db_account)
    db.commit()
    return None
