
import time
import random
import requests
from datetime import datetime
from typing import Dict, List, Optional
from app.database import SessionLocal
from app.models.task import Task
from app.models.raw_data import RawData
from app.models.proxy import Proxy
from app.models.account import Account
from app.utils.redis import get_redis
from app.config import settings
import json
import re
from bs4 import BeautifulSoup
from app.services.crawler_task import ControlledSpider

# 全局爬虫实例管理器
crawler_instances = {}

def run_crawler_task(task_id: int, url: str = None, interval: int = 5, 
                     restart_interval: int = 3600, time_range: tuple = (0, 24),
                     browser_type: str = "chromium", max_exception: int = 3):
    """运行小鲸鱼任务，使用 ControlledSpider"""
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
        
        # 获取爬虫参数
        crawler_param = None
        if task.crawler_param_id:
            from app.models.crawler_param import CrawlerParam
            crawler_param = db.query(CrawlerParam).filter(CrawlerParam.id == task.crawler_param_id).first()

        # 使用爬虫参数或默认值
        crawl_url = url or (crawler_param.url if crawler_param else "https://www.baidu.com")
        crawl_interval = interval or (crawler_param.interval if crawler_param else 5)
        crawl_restart_interval = restart_interval or (crawler_param.restart_interval if crawler_param else 3600)
        crawl_time_range = time_range or (crawler_param.time_range if crawler_param else (0, 24))
        crawl_browser_type = browser_type or (crawler_param.browser_type if crawler_param else "chromium")
        crawl_max_exception = max_exception or (crawler_param.max_exception if crawler_param else 3)

        # 创建 ControlledSpider 实例
        spider = ControlledSpider(
            interval=crawl_interval,
            restart_interval=crawl_restart_interval,
            time_range=crawl_time_range,
            browser_type=crawl_browser_type,
            max_exception=crawl_max_exception
        )

        # 保存到全局管理器
        crawler_instances[task_id] = spider

        # 启动爬虫（在后台线程中运行异步任务）
        import asyncio
        import threading
        
        # 存储事件循环以便后续清理
        spider_loop = None
        
        def run_spider():
            nonlocal spider_loop
            spider_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(spider_loop)
            try:
                spider_loop.run_until_complete(spider.start(crawl_url))
            except asyncio.CancelledError:
                print(f"任务 {task_id} 的爬虫被取消")
            finally:
                # 等待所有待处理的任务完成
                pending = asyncio.all_tasks(spider_loop)
                if pending:
                    spider_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                spider_loop.close()
        
        thread = threading.Thread(target=run_spider, daemon=True)
        thread.start()
        print(f"任务 {task_id} 的爬虫已启动")

        # 更新任务状态为运行中
        task.status = 1
        task.start_time = datetime.now()
        db.commit()

        # 监控任务状态
        while spider.is_running():
            db.refresh(task)
            if task.status != 1:  # 任务被停止
                spider.stop()
                print(f"任务 {task_id} 已停止")
                # 等待线程完成，确保事件循环正确关闭
                if thread.is_alive():
                    thread.join(timeout=5)
                break
            time.sleep(1)

        # 任务结束
        if task.status == 1:  # 如果是爬虫自己停止的
            task.status = 4  # 完成
            task.end_time = datetime.now()
            task.progress = 100
            db.commit()

    except Exception as e:
        print(f"小鲸鱼任务异常: {str(e)}")
        task.status = 3  # 失败
        task.error_message = str(e)
        task.end_time = datetime.now()
        task.retry_count += 1
        db.commit()

    finally:
        # 确保爬虫已停止
        if spider.is_running():
            try:
                # 在新的事件循环中运行stop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(spider.stop())
                loop.close()
            except Exception as e:
                print(f"停止爬虫时出错: {str(e)}")
        
        # 等待线程完成
        if thread.is_alive():
            thread.join(timeout=5)
        
        # 从全局管理器中移除
        if task_id in crawler_instances:
            del crawler_instances[task_id]
        db.close()



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

def stop_crawler_task(task_id: int):
    """停止指定任务的爬虫"""
    if task_id in crawler_instances:
        spider = crawler_instances[task_id]
        spider.stop()
        print(f"任务 {task_id} 的爬虫已停止")
        return True
    return False

def is_crawler_running(task_id: int) -> bool:
    """检查指定任务的爬虫是否在运行"""
    if task_id in crawler_instances:
        return crawler_instances[task_id].is_running()
    return False
