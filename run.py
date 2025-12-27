
import uvicorn
import signal
import sys

if __name__ == "__main__":
    from app.config import settings
    
    # 创建一个标志来控制程序退出
    should_exit = False
    
    def handle_shutdown(signum, frame):
        global should_exit
        print("\n正在关闭服务器...")
        should_exit = True
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # 配置 uvicorn
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=False,
        workers=1
    )
    server = uvicorn.Server(config)
    
    # 运行服务器
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在关闭服务器...")
        server.should_exit = True
    finally:
        print("服务器已关闭")
