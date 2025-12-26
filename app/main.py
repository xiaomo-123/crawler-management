
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.api import accounts, tasks, proxies, quotas, raw_data, sample_data, exports, redis_configs, utils, crawler_params, recommendations, qa_crawler
from app.models.crawler_param import CrawlerParam
from app.config import settings
from app.database import init_db
from app.utils.redis import init_redis
from app.services.heartbeat_new import heartbeat_service
from app.workers.qa_crawler_consumer import qa_crawler_consumer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    init_db()
    

    # 初始化Redis
    init_redis()

    # 启动QA爬虫消费者
    await qa_crawler_consumer.start()

    # 初始化并启动心跳服务
    heartbeat_service.init_app(app)
    heartbeat_service.start()

    yield

    # 关闭时执行（如果需要）
    await qa_crawler_consumer.stop()
    print("应用关闭")

def create_app():
    """创建FastAPI应用"""
    # 创建FastAPI应用
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="爬虫任务&API任务SQLite管理系统",
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # 注册API路由
    app.include_router(accounts.router)
    app.include_router(tasks.router)
    app.include_router(proxies.router)
    app.include_router(quotas.router)
    app.include_router(raw_data.router)
    app.include_router(sample_data.router)
    app.include_router(exports.router)
    app.include_router(redis_configs.router)
    app.include_router(utils.router)
    app.include_router(crawler_params.router)
    app.include_router(recommendations.router)
    app.include_router(qa_crawler.router)

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # 根路径返回首页
    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    return app

# 创建应用实例
app = create_app()
