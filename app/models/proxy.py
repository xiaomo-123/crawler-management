
from sqlalchemy import Column, Integer, String
from app.database import Base

class Proxy(Base):
    __tablename__ = "proxy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy_type = Column(String(10), nullable=False, comment="代理类型：HTTP/HTTPS/SOCKS")
    proxy_addr = Column(String(255), unique=True, nullable=False, comment="代理地址:端口")
    status = Column(Integer, default=1, nullable=False, comment="状态：1-正常，0-禁用")
    strategy = Column(String(20), default="轮询", nullable=False, comment="策略：轮询/随机/失败切换")

    def __repr__(self):
        return f"<Proxy(id={self.id}, type={self.proxy_type}, addr={self.proxy_addr}, status={self.status})>"
