
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List
from app.database import SessionLocal
from app.models.sample_data import SampleData
from app.models.raw_data import RawData
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
def export_RawData_data_to_excel() -> str:
    db = SessionLocal()

    try:
        # 获取年份配额信息
        quotas = db.query(YearQuota).all()
        quota_dict = {}
        for quota in quotas:
            # 为配额范围内的每个年份添加配额信息
            for year in range(quota.start_year, quota.end_year + 1):
                quota_dict[year] = {"stock_ratio": quota.stock_ratio, "sample_num": quota.sample_num}

        # 按年份范围抽样数据
        all_sampled_data = []
        for quota in quotas:
            # 获取该年份范围内的所有原始数据
            raw_data_list = db.query(RawData).filter(
                RawData.year >= quota.start_year,
                RawData.year <= quota.end_year
            ).all()

            # 按年份分组
            raw_data_by_year = {}
            for data in raw_data_list:
                if data.year not in raw_data_by_year:
                    raw_data_by_year[data.year] = []
                raw_data_by_year[data.year].append(data)

            # 按年份抽样
            for year, year_data in raw_data_by_year.items():
                sample_num = quota_dict.get(year, {}).get("sample_num", 0)
                if sample_num > 0 and len(year_data) > sample_num:
                    import random
                    sampled_year_data = random.sample(year_data, sample_num)
                else:
                    sampled_year_data = year_data

                # 打印年份和抽样数据
                print(f"年份: {year}, 抽样数量: {len(sampled_year_data)}")

                # 获取关联的评论数据
                for data in sampled_year_data:
                    print(f"RawData ID: {data.id}, 标题: {data.title}")

                    # 从原始数据的publish_time字段提取年月
                    publish_time = data.publish_time
                    if publish_time:
                        # publish_time是字符串格式，使用"-"符号分割
                        if isinstance(publish_time, str):
                            parts = publish_time.split('-')
                            if len(parts) >= 2:
                                comment_year = int(parts[0])
                                comment_month = int(parts[1])
                            else:
                                # 如果格式不正确，使用year字段
                                comment_year = data.year
                                comment_month = 1  # 默认为1月
                        else:
                            # 如果不是字符串，使用year字段
                            comment_year = data.year
                            comment_month = 1  # 默认为1月
                    else:
                        # 如果没有publish_time，使用year字段
                        comment_year = data.year
                        comment_month = 1  # 默认为1月

                    # 获取对应年月的评论分表模型
                    from app.models.comment_data import CommentDataFactory
                    comment_model = CommentDataFactory.get_model(comment_year, comment_month)

                    # 从对应年月的评论分表查询评论
                    comments = db.query(comment_model).filter(comment_model.raw_data_id == data.id).all()

                    print(f"  关联评论数量: {len(comments)}")
                    for comment in comments:
                        print(f"  评论ID: {comment.id}, 作者: {comment.author}, 内容: {comment.content[:50]}...")

                    # 添加到抽样数据列表
                    all_sampled_data.append(data)

        # 转换数据为DataFrame
        data = []
        for item in all_sampled_data:
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
        filename = f"raw_data_{timestamp}.xlsx"
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
