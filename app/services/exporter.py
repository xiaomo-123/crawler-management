
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List
from app.database import SessionLocal
from app.models.sample_data import SampleData
from app.models.year_quota import YearQuota
from app.models.task import Task
from app.config import settings

def run_export_task(task_id: int) -> bool:
    """运行导出任务"""
    db = SessionLocal()

    try:
        # 获取任务信息
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"任务ID {task_id} 不存在")
            return False

        # 获取所有抽样数据
        sample_data_list = db.query(SampleData).all()
        if not sample_data_list:
            print("没有抽样数据可导出")
            task.status = 3  # 失败
            task.error_message = "没有抽样数据可导出"
            task.end_time = datetime.now()
            db.commit()
            return False

        # 获取年份配额信息
        quotas = db.query(YearQuota).all()
        quota_dict = {}
        for quota in quotas:
            # 为配额范围内的每个年份添加配额信息
            for year in range(quota.start_year, quota.end_year + 1):
                quota_dict[year] = {"stock_ratio": quota.stock_ratio, "sample_num": quota.sample_num}

        # 转换数据为DataFrame
        data = []
        for item in sample_data_list:
            data.append({
                "标题": item.title,
                "内容": item.content,
                "发布时间": item.publish_time,
                "回答链接": item.answer_url,
                "作者": item.author,
                "作者链接": item.author_url,
                "作者领域": item.author_field,
                "作者认证": item.author_cert,
                "作者粉丝数": item.author_fans,
                "年份": item.year,
                "存量占比": quota_dict.get(item.year, {}).get("stock_ratio", 0),
                "抽样条数": quota_dict.get(item.year, {}).get("sample_num", 0)
            })

        df = pd.DataFrame(data)

        # 创建导出目录
        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sample_data_{timestamp}.xlsx"
        filepath = os.path.join(export_dir, filename)

        # 导出到Excel
        df.to_excel(filepath, index=False)

        # 更新任务状态
        task.status = 4  # 完成
        task.end_time = datetime.now()
        task.progress = 100
        db.commit()

        print(f"导出完成: {filepath}")
        return True

    except Exception as e:
        print(f"导出任务异常: {str(e)}")
        task.status = 3  # 失败
        task.error_message = str(e)
        task.end_time = datetime.now()
        task.retry_count += 1
        db.commit()
        return False

    finally:
        db.close()

def export_sample_data_to_excel() -> str:
    """导出抽样数据到Excel"""
    db = SessionLocal()

    try:
        # 获取所有抽样数据
        sample_data_list = db.query(SampleData).all()
        if not sample_data_list:
            print("没有抽样数据可导出")
            return ""

        # 获取年份配额信息
        quotas = db.query(YearQuota).all()
        quota_dict = {}
        for quota in quotas:
            # 为配额范围内的每个年份添加配额信息
            for year in range(quota.start_year, quota.end_year + 1):
                quota_dict[year] = {"stock_ratio": quota.stock_ratio, "sample_num": quota.sample_num}

        # 转换数据为DataFrame
        data = []
        for item in sample_data_list:
            data.append({
                "标题": item.title,
                "内容": item.content,
                "发布时间": item.publish_time,
                "回答链接": item.answer_url,
                "作者": item.author,
                "作者链接": item.author_url,
                "作者领域": item.author_field,
                "作者认证": item.author_cert,
                "作者粉丝数": item.author_fans,
                "年份": item.year,
                "存量占比": quota_dict.get(item.year, {}).get("stock_ratio", 0),
                "抽样条数": quota_dict.get(item.year, {}).get("sample_num", 0)
            })

        df = pd.DataFrame(data)

        # 创建导出目录
        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sample_data_{timestamp}.xlsx"
        filepath = os.path.join(export_dir, filename)

        # 导出到Excel
        df.to_excel(filepath, index=False)

        print(f"导出完成: {filepath}")
        return filepath

    except Exception as e:
        print(f"导出异常: {str(e)}")
        return ""

    finally:
        db.close()

def get_export_files() -> List[Dict]:
    """获取导出文件列表"""
    export_dir = os.path.join(os.getcwd(), "exports")
    if not os.path.exists(export_dir):
        return []

    files = []
    for filename in os.listdir(export_dir):
        if filename.endswith(".xlsx"):
            filepath = os.path.join(export_dir, filename)
            stat = os.stat(filepath)
            files.append({
                "filename": filename,
                "filepath": filepath,
                "size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            })

    # 按创建时间倒序排列
    files.sort(key=lambda x: x["created_time"], reverse=True)

    return files
