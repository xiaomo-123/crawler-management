
import uvicorn

if __name__ == "__main__":
    from app.config import settings
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 完全禁用重载
        workers=1  # 禁用多进程模式
    )
