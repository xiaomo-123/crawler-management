
import uvicorn
from app.main import app

if __name__ == "__main__":
    from app.config import settings
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1  # 设置为单进程避免多进程问题
    )
