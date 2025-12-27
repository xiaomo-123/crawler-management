import asyncio
import time
from app.database import SessionLocal
from app.services.qa_crawler import qa_crawler_service

class QACrawlerConsumer:
    def __init__(self):
        self.running = False
        self.task = None
    
    async def start(self):
        """启动消费者"""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._consume())
    
    async def stop(self):
        """停止消费者"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _consume(self):
        """消费队列"""
        db = SessionLocal()
        try:
            while self.running:
                try:
                    result = qa_crawler_service.process_queue(db, 10)
                    print(f"处理队列结果: 已处理 {result['processed']} 条, 失败 {result['failed']} 条")
                except asyncio.CancelledError:
                    print("消费者任务被取消，正在关闭...")
                    break
                except Exception as e:
                    print(f"处理队列时发生错误: {str(e)}")
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            print("消费者任务被取消，正在关闭...")
        finally:
            db.close()

# 创建消费者实例
qa_crawler_consumer = QACrawlerConsumer()
