
import random
from typing import List
from app.database import SessionLocal
from app.models.raw_data import RawData
from app.models.sample_data import SampleData
from app.models.year_quota import YearQuota

def sample_data_by_quota() -> bool:
    """按配额抽样数据"""
    db = SessionLocal()

    try:
        # 获取所有年份配额
        quotas = db.query(YearQuota).all()
        if not quotas:
            print("没有找到年份配额")
            return False

        # 清空现有抽样数据
        db.query(SampleData).delete()
        db.commit()

        # 按年份抽样数据
        for quota in quotas:
            # 获取该年份的所有原始数据
            raw_data_list = db.query(RawData).filter(RawData.year == quota.year).all()

            # 如果原始数据不足，则全部抽取
            if len(raw_data_list) <= quota.sample_num:
                sample_list = raw_data_list
            else:
                # 随机抽样
                sample_list = random.sample(raw_data_list, quota.sample_num)

            # 将抽样数据插入到sample_data表
            for raw_data in sample_list:
                sample_data = SampleData(
                    title=raw_data.title,
                    content=raw_data.content,
                    publish_time=raw_data.publish_time,
                    answer_url=raw_data.answer_url,
                    author=raw_data.author,
                    author_url=raw_data.author_url,
                    author_field=raw_data.author_field,
                    author_cert=raw_data.author_cert,
                    author_fans=raw_data.author_fans,
                    year=raw_data.year,
                    task_id=raw_data.task_id
                )
                db.add(sample_data)

        db.commit()
        return True

    except Exception as e:
        print(f"抽样数据异常: {str(e)}")
        db.rollback()
        return False

    finally:
        db.close()

def get_sample_stats() -> dict:
    """获取抽样统计信息"""
    db = SessionLocal()

    try:
        # 按年份统计抽样数据
        from sqlalchemy import func
        stats = db.query(
            SampleData.year,
            func.count(SampleData.id).label("count")
        ).group_by(SampleData.year).all()

        # 转换为字典格式
        result = {str(year): count for year, count in stats}

        # 获取总抽样数
        total = db.query(func.count(SampleData.id)).scalar()
        result["total"] = total

        return result

    except Exception as e:
        print(f"获取抽样统计异常: {str(e)}")
        return {}

    finally:
        db.close()
