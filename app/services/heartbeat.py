import asyncio
import httpx
from datetime import datetime
from app.config import settings

class HeartbeatService:
    def __init__(self):
        self.is_running = False
        self.heartbeat_task = None
        self.heartbeat_url = f"http://localhost:{settings.PORT}/api/utils/heartbeat"
        self.client = None
        self.app_ready = False

    async def send_heartbeat(self):
        """发送心跳请求"""
        if not self.client:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳客户端未初始化")
            return False
        
        try:            
            response = await self.client.get(self.heartbeat_url)                
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳正常")
                return True
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳异常: {response.status_code}")
        except httpx.TimeoutException:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳超时")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳失败: {str(e)}")
        return False

    async def heartbeat_loop(self):
        """心跳循环"""
        # 等待应用完全启动
        await asyncio.sleep(15)
        # 先尝试发送几次心跳，确保应用已完全启动
        for _ in range(3):
            await self.send_heartbeat()
            await asyncio.sleep(2)
        # 正常心跳循环
        while self.is_running:
            await self.send_heartbeat()
            await asyncio.sleep(5)  # 每5秒发送一次心跳

    async def start(self):
        """启动心跳服务"""
        if not self.is_running:
            self.is_running = True
            # 创建复用的客户端
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            # 等待应用完全启动
            await asyncio.sleep(5)
            self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            print("心跳服务已启动")

    async def stop(self):
        """停止心跳服务"""
        if self.is_running:
            self.is_running = False
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            if self.client:
                await self.client.aclose()
                self.client = None
            print("心跳服务已停止")

# 创建全局心跳服务实例
heartbeat_service = HeartbeatService()
