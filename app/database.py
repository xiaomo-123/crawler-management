
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("数据库初始化成功")
    except Exception as e:
        # 忽略索引已存在的错误
        if "already exists" in str(e):
            print("数据库已存在，跳过初始化")
        else:
            raise e

    # 检查并更新account表的UNIQUE约束
    from sqlalchemy import inspect, text
    inspector = inspect(engine)

    # 检查account表是否存在
    if 'account' in inspector.get_table_names():
        # 获取account表的索引
        indexes = inspector.get_indexes('account')

        # 查找account_name的唯一索引
        unique_indexes = [idx for idx in indexes if idx.get('unique', False) and 'account_name' in idx.get('column_names', [])]

        # 如果存在唯一索引,则删除它
        if unique_indexes:
            with engine.connect() as conn:
                for idx in unique_indexes:
                    try:
                        conn.execute(text(f"DROP INDEX {idx['name']}"))
                        conn.commit()
                        print(f"已删除索引: {idx['name']}")
                    except Exception as e:
                        print(f"删除索引失败: {e}")
