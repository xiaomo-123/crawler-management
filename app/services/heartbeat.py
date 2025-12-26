import asyncio
import httpx
from datetime import datetime
from app.config import settings

class HeartbeatService:
    def __init__(self):
        self.is_running = False
        self.heartbeat_task = None
        self.heartbeat_url = f"http://127.0.0.1:{settings.PORT}/api/utils/heartbeat"

    async def send_heartbeat(self):
        """发送心跳请求"""
        try:            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.heartbeat_url, timeout=5.0)                
                if response.status_code == 200:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳正常")
                    return True
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳异常: {response.status_code}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳失败: {str(e)}")
        return False

    async def heartbeat_loop(self):
        """心跳循环"""
        # 等待应用完全启动
        await asyncio.sleep(3)
        while self.is_running:
            await self.send_heartbeat()
            await asyncio.sleep(5)  # 每5秒发送一次心跳

    async def start(self):
        """启动心跳服务"""
        if not self.is_running:
            self.is_running = True
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
            print("心跳服务已停止")

# 创建全局心跳服务实例
heartbeat_service = HeartbeatService()
