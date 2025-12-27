
import os
import pandas as pd
import time
import random
import requests
from datetime import datetime
from typing import Dict, List, Optional
from app.database import SessionLocal
from app.models.sample_data import SampleData
from app.models.raw_data import RawData
from app.models.year_quota import YearQuota
from app.models.task import Task
from app.models.proxy import Proxy
from app.models.account import Account
from app.utils.redis import get_redis
from app.config import settings
import json
import re
from bs4 import BeautifulSoup
from app.services.exporter_task import ControlledExporter

# 全局导出实例管理器
exporter_instances = {}

def run_export_task(task_id: int, url: str = None, api_request: str = None, task_type: str = "export",
                     interval: int = 5,
                     restart_interval: int = 3600, time_range: tuple = (0, 24),
                     max_exception: int = 3):
    """运行导出任务，使用 ControlledExporter"""
    db = SessionLocal()

    try:
        # 获取任务信息
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"任务ID {task_id} 不存在")
            return

        # 获取账号信息
        account = db.query(Account).filter(Account.id == task.account_id).first()
        if not account:
            print(f"账号ID {task.account_id} 不存在")
            task.status = 3  # 失败
            task.error_message = f"账号ID {task.account_id} 不存在"
            task.end_time = datetime.now()
            db.commit()
            return

        # 获取导出参数
        export_param = None
        if task.crawler_param_id:
            from app.models.crawler_param import CrawlerParam
            export_param = db.query(CrawlerParam).filter(CrawlerParam.id == task.crawler_param_id).first()

        # 使用导出参数或默认值
        export_url = url or (export_param.url if export_param else "https://www.baidu.com")
        export_api_request = api_request or (export_param.api_request if export_param else None)
        export_task_type = task_type or (export_param.task_type if export_param else "export")
        export_interval = interval or (export_param.interval_time * 3600 if export_param else 5 * 3600)  # 转换为秒
        export_restart_interval = restart_interval or (export_param.restart_browser_time * 3600 if export_param else 24 * 3600)  # 转换为秒
        export_time_range = time_range or ((export_param.start_time, export_param.end_time) if export_param else (0, 24))
        export_max_exception = max_exception or (export_param.error_count if export_param else 3)

        # 获取账号cookie
        account_cookie = account.account_name if account else None

        # 获取代理信息
        proxy = None
        proxy_obj = db.query(Proxy).filter(Proxy.status == 1).first()
        if proxy_obj:
            proxy = f"{proxy_obj.proxy_type}://{proxy_obj.proxy_addr}"

        # 创建 ControlledExporter 实例
        exporter = ControlledExporter(
            interval=export_interval,
            restart_interval=export_restart_interval,
            time_range=export_time_range,
            max_exception=export_max_exception,
            api_request=export_api_request,
            task_type=export_task_type,
            storage_state_path="cook"+ str(account.id),            
            proxy=proxy,
            cookie=account_cookie,
            account_id=account.id,
        )

        # 打印中文参数信息
        print(f"任务 {task_id} 导出配置:")
        print(f"  URL地址: {export_url}")
        print(f"  API请求: {export_api_request}")
        print(f"  任务类型: {export_task_type}")
        print(f"  间隔时间: {export_interval // 3600} 小时")
        print(f"  重启浏览器时间: {export_restart_interval // 3600} 小时")
        print(f"  时间范围: {export_time_range[0]}:00 - {export_time_range[1]}:00")
        print(f"  最大异常次数: {export_max_exception}")
        print(f"  cookie路径: {exporter.storage_state_path}")
        print(f"  代理: {exporter.proxy}")
        print(f"  cookie: {account_cookie}")
        # 保存到全局管理器
        exporter_instances[task_id] = exporter

        # 启动导出（在后台线程中运行异步任务）
        import asyncio
        import threading

        # 存储事件循环以便后续清理
        exporter_loop = None

        def run_exporter():
            nonlocal exporter_loop
            exporter_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(exporter_loop)
            try:
                exporter_loop.run_until_complete(exporter.start(export_url))
            except asyncio.CancelledError:
                print(f"任务 {task_id} 的导出被取消")
            finally:
                # 等待所有待处理的任务完成
                pending = asyncio.all_tasks(exporter_loop)
                if pending:
                    exporter_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                exporter_loop.close()

        thread = threading.Thread(target=run_exporter, daemon=True)
        thread.start()
        print(f"任务 {task_id} 的导出已启动")

        # 更新任务状态为运行中
        task.status = 1
        task.start_time = datetime.now()
        db.commit()

        # 监控任务状态
        while exporter.is_running():
            db.refresh(task)
            if task.status != 1:  # 任务被停止
                # 使用同步停止方法
                exporter.stop_sync()
                print(f"任务 {task_id} 已停止")
                # 等待线程完成，确保事件循环正确关闭
                if thread.is_alive():
                    thread.join(timeout=5)
                break
            time.sleep(1)

        # 任务结束
        if task.status == 1:  # 如果是导出自己停止的
            task.status = 4  # 完成
            task.end_time = datetime.now()
            task.progress = 100
            db.commit()

    except Exception as e:
        print(f"导出任务异常: {str(e)}")
        task.status = 3  # 失败
        task.error_message = str(e)
        task.end_time = datetime.now()
        task.retry_count += 1
        db.commit()

    finally:
        # 确保导出已停止
        if exporter.is_running():
            try:
                # 使用同步停止方法
                exporter.stop_sync()
            except Exception as e:
                print(f"停止导出时出错: {str(e)}")

        # 等待线程完成
        if thread.is_alive():
            thread.join(timeout=5)

        # 从全局管理器中移除
        if task_id in exporter_instances:
            del exporter_instances[task_id]
        db.close()

def run_export_task_to_excel(task_id: int) -> bool:
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
        quota = db.query(YearQuota).first()
        if not quota:
            print("未查询到任何配额数据，无法导出")
            return ""
        
        years = range(quota.start_year, quota.end_year + 1)


        # 创建导出目录
        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_data_{timestamp}.xlsx"
        filepath = os.path.join(export_dir, filename)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for year in years:
                # 按年份获取抽样数据
                sampled_data = get_sampled_data_with_comment(db, year)
                if not sampled_data:
                    continue

                # 转换为DataFrame
                data = [{
                    "id": item.id,
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
                    "评论者": item.comment_details
                } for item in sampled_data]

                year_df = pd.DataFrame(data)
                year_df.to_excel(writer, sheet_name=f"{year}年", index=False)
                worksheet = writer.sheets[f"{year}年"]
                # 对"评论者"列设置自动换行（假设列索引为10，可根据实际列顺序调整）
                comment_col = year_df.columns.get_loc("评论者") + 1  # pandas列索引从0开始，Excel从1开始
                for cell in worksheet[comment_col]:
                    cell.alignment = cell.alignment.copy(wrap_text=True)  # 启用自动换行
                
                # 调整列宽以适应内容（可选）
                worksheet.column_dimensions[chr(65 + comment_col)].width = 50  # 65是'A'的ASCII码

                

        print(f"导出完成: {filepath}")
        return filepath

    except Exception as e:
        print(f"导出异常: {str(e)}")
        return ""

    finally:
        db.close()
def get_sampled_data_with_comment(db, year):
    """按年份分批获取抽样数据及评论（单次处理一个年份）"""
    # 获取当前年份的配额
    quota = db.query(YearQuota).filter(
        year >= YearQuota.start_year,
        year <= YearQuota.end_year
    ).first()
    
    if not quota:
        print(f"年份 {year} 未查询到配额数据")
        return []
    
    sample_num = quota.sample_num
    if sample_num <= 0:
        print(f"年份 {year} 抽样数量为0，跳过处理")
        return []

    # 分页查询当前年份的原始数据
    page_size = 1000  # 固定分页大小，避免内存占用过大
    offset = 0
    year_data = []
    
    while True:
        batch = db.query(RawData).filter(
            RawData.year == year
        ).limit(page_size).offset(offset).all()
        
        if not batch:
            break  # 分页结束
        
        year_data.extend(batch)
        offset += page_size
       

    # 执行抽样
    if len(year_data) > sample_num:
        import random
        sampled_year_data = random.sample(year_data, sample_num)
    else:
        sampled_year_data = year_data
    
    

    # 关联评论数据
    for data in sampled_year_data:
        # 提取发布时间中的年月信息
        publish_time = data.publish_time
        if publish_time and isinstance(publish_time, str):
            parts = publish_time.split('-')
            if len(parts) >= 2:
                comment_year, comment_month = int(parts[0]), int(parts[1])
            else:
                comment_year, comment_month = data.year, 1
        else:
            comment_year, comment_month = data.year, 1

        # 获取对应年月的评论模型并查询
        from app.models.comment_data import CommentDataFactory
        comment_model = CommentDataFactory.get_model(comment_year, comment_month)
        comments = db.query(comment_model).filter(comment_model.raw_data_id == data.id).all()

        # 格式化评论信息
        comment_details = []
        for comment in comments:
            comment_info = (
                f"作者: {comment.author or '未知'}  "  # 用空格替代换行
                f"作者链接: {comment.author_url or '无'}  "
                f"内容: {comment.content or '无'}  "
                f"点赞数: {comment.like_count or 0}  "
                f"时间: {comment.time or '未知'}"
            )
            comment_details.append(comment_info)
        
        data.comment_details = "\n".join(comment_details) if comment_details else "无评论"

    return sampled_year_data        
def get_sampled_data_with_comments(db):    
    quota = db.query(YearQuota).first()    
    # 空值判断，直接返回空字典
    if not quota:
        print("未查询到配额数据")
        return []
    
    # 生成配额字典
    quota_dict = {}
    for year in range(quota.start_year, quota.end_year + 1):
        quota_dict[year] = {
            "stock_ratio": quota.stock_ratio,
            "sample_num": quota.sample_num
        }
    # 按年份范围抽样数据
    all_sampled_data = []
    # 1. 确定需要处理的年份范围
    years = range(quota.start_year, quota.end_year + 1)
    # 2. 按年份分片处理（每个年份单独查询，避免一次性加载所有年份数据）
    for year in years:
        sample_num = quota_dict.get(year, {}).get("sample_num", 0)
        if sample_num <= 0:
            continue  # 无需抽样，跳过该年份
        
        # 3. 单年份内分页查询（每次查1000条，可根据内存调整）
        page_size = int(sample_num)  # 每页条数，按需调整
        offset = 0
        year_data = []  # 存储当前年份的所有数据（分页累计）
        
        while True:
            # 分页查询当前年份的数据
            batch = db.query(RawData).filter(
                RawData.year == year  # 只查当前年份
            ).limit(page_size).offset(offset).all()
            
            if not batch:
                break  # 分页结束，没有更多数据
            
            year_data.extend(batch)
            offset += page_size  # 偏移量累加，准备下一页
            
            # 可选：打印分页进度
            
        
        # 4. 对当前年份的所有数据进行抽样
        if len(year_data) > sample_num:
            import random
            sampled_year_data = random.sample(year_data, sample_num)
        else:
            sampled_year_data = year_data
        
        
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
            comment_details = []
            for comment in comments:
                print(f"  评论ID: {comment.id}, 作者: {comment.author}, 内容: {comment.content[:50]}...")
                comment_info = (
                    f"作者: {comment.author or '未知'}\n"
                    f"作者链接: {comment.author_url or '无'}\n"
                    f"内容: {comment.content or '无'}\n"
                    f"点赞数: {comment.like_count or 0}\n"
                    f"时间: {comment.time or '未知'}"
                )
                comment_details.append(comment_info)
            data.comment_details = "\n\n" + "\n\n".join(comment_details) if comment_details else "无评论"    
            # 添加到抽样数据列表
            all_sampled_data.append(data)
    
    return all_sampled_data

def get_sampled_data_with_commentg(db):    
    quota = db.query(YearQuota).first()    
    # 空值判断，直接返回空字典
    if not quota:
        print("未查询到配额数据")
        return []
    
    # 生成配额字典
    quota_dict = {}
    for year in range(quota.start_year, quota.end_year + 1):
        quota_dict[year] = {
            "stock_ratio": quota.stock_ratio,
            "sample_num": quota.sample_num
        }
    # 按年份范围抽样数据
    all_sampled_data = []
    # 1. 确定需要处理的年份范围
    years = range(quota.start_year, quota.end_year + 1)
    # 2. 按年份分片处理（每个年份单独查询，避免一次性加载所有年份数据）
    for year in years:
        sample_num = quota_dict.get(year, {}).get("sample_num", 0)
        if sample_num <= 0:
            continue  # 无需抽样，跳过该年份
        
        # 3. 单年份内分页查询（每次查1000条，可根据内存调整）
        page_size = int(sample_num)  # 每页条数，按需调整
        offset = 0
        year_data = []  # 存储当前年份的所有数据（分页累计）
        
        while True:
            # 分页查询当前年份的数据
            batch = db.query(RawData).filter(
                RawData.year == year  # 只查当前年份
            ).limit(page_size).offset(offset).all()
            
            if not batch:
                break  # 分页结束，没有更多数据
            
            year_data.extend(batch)
            offset += page_size  # 偏移量累加，准备下一页
            
            # 可选：打印分页进度
            print(f"年份 {year} 已加载 {len(year_data)} 条数据（分页偏移：{offset}）")
        
        # 4. 对当前年份的所有数据进行抽样
        if len(year_data) > sample_num:
            import random
            sampled_year_data = random.sample(year_data, sample_num)
        else:
            sampled_year_data = year_data
        
        print(f"年份: {year}, 总数据量: {len(year_data)}, 抽样数量: {len(sampled_year_data)}")
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
            comment_details = []
            for comment in comments:
                print(f"  评论ID: {comment.id}, 作者: {comment.author}, 内容: {comment.content[:50]}...")
                comment_info = (
                    f"作者: {comment.author or '未知'}\n"
                    f"作者链接: {comment.author_url or '无'}\n"
                    f"内容: {comment.content or '无'}\n"
                    f"点赞数: {comment.like_count or 0}\n"
                    f"时间: {comment.time or '未知'}"
                )
                comment_details.append(comment_info)
            data.comment_details = "\n\n" + "\n\n".join(comment_details) if comment_details else "无评论"    
            # 添加到抽样数据列表
            all_sampled_data.append(data)
    
    return all_sampled_data


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

def select_proxy(proxies: List[Proxy]) -> Optional[Proxy]:
    """选择代理"""
    if not proxies:
        return None

    # 过滤可用代理
    available_proxies = [p for p in proxies if p.status == 1]
    if not available_proxies:
        return None

    # 根据策略选择代理
    strategy = available_proxies[0].strategy  # 使用第一个代理的策略

    if strategy == "轮询":
        # 简单轮询，每次选择第一个
        return available_proxies[0]
    elif strategy == "随机":
        return random.choice(available_proxies)
    elif strategy == "失败切换":
        # 选择最近未失败的代理
        return available_proxies[0]

    return available_proxies[0]

def parse_page(html: str, url: str) -> Optional[Dict]:
    """解析页面内容"""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # 提取标题
        title_elem = soup.find("h1", class_="QuestionHeader-title")
        title = title_elem.text.strip() if title_elem else ""

        # 提取内容
        content_elem = soup.find("div", class_="RichContent-inner")
        content = content_elem.text.strip() if content_elem else ""

        # 提取发布时间
        time_elem = soup.find("span", class_="ContentItem-time")
        publish_time = ""
        if time_elem:
            time_text = time_elem.text.strip()
            # 尝试提取日期
            match = re.search(r"(\d{4}-\d{2}-\d{2})", time_text)
            if match:
                publish_time = match.group(1)

        # 提取作者信息
        author_elem = soup.find("div", class_="AuthorInfo")
        author = ""
        author_url = ""
        author_field = ""
        author_cert = ""
        author_fans = 0

        if author_elem:
            # 作者名
            name_elem = author_elem.find("a", class_="UserLink-link")
            if name_elem:
                author = name_elem.text.strip()
                author_url = "https://www.zhihu.com" + name_elem.get("href", "")

            # 作者领域
            field_elem = author_elem.find("div", class_="AuthorInfo-badgeText")
            if field_elem:
                author_field = field_elem.text.strip()

            # 作者认证
            cert_elem = author_elem.find("div", class_="AuthorInfo-headline")
            if cert_elem:
                author_cert = cert_elem.text.strip()

            # 作者粉丝数
            fans_elem = author_elem.find("div", class_="NumberBoard-itemValue")
            if fans_elem:
                try:
                    fans_text = fans_elem.text.strip()
                    # 处理粉丝数中的"万"等单位
                    if "万" in fans_text:
                        author_fans = int(float(fans_text.replace("万", "")) * 10000)
                    else:
                        author_fans = int(fans_text)
                except:
                    author_fans = 0

        return {
            "title": title,
            "content": content,
            "publish_time": publish_time,
            "author": author,
            "author_url": author_url,
            "author_field": author_field,
            "author_cert": author_cert,
            "author_fans": author_fans,
        }

    except Exception as e:
        print(f"解析页面异常: {str(e)}, URL: {url}")
        return None

def extract_year(publish_time: str) -> int:
    """从发布时间中提取年份"""
    if not publish_time:
        return 2023  # 默认年份

    # 尝试从YYYY-MM-DD格式中提取年份
    match = re.search(r"(\d{4})-\d{2}-\d{2}", publish_time)
    if match:
        return int(match.group(1))

    # 尝试从其他格式中提取年份
    match = re.search(r"(\d{4})年", publish_time)
    if match:
        return int(match.group(1))

    # 默认返回当前年份
    return datetime.now().year

def stop_export_task(task_id: int):
    """停止指定任务的导出"""
    if task_id in exporter_instances:
        exporter = exporter_instances[task_id]
        exporter.stop_sync()
        print(f"任务 {task_id} 的导出已停止")
        return True
    return False

def is_export_running(task_id: int) -> bool:
    """检查指定任务的导出是否在运行"""
    if task_id in exporter_instances:
        return exporter_instances[task_id].is_running()
    return False
