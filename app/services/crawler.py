
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

def run_crawler_task(task_id: int):
    """运行小鲸鱼任务"""
    db = SessionLocal()
    redis = get_redis()

    try:
        # 获取任务信息
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"任务ID {task_id} 不存在")
            return

        # 获取账号信息
        account = db.query(Account).filter(Account.account_name == task.account_name).first()
        if not account:
            print(f"账号 {task.account_name} 不存在")
            task.status = 3  # 失败
            task.error_message = f"账号 {task.account_name} 不存在"
            task.end_time = datetime.now()
            db.commit()
            return
        
        # 获取代理列表
        proxies = db.query(Proxy).filter(Proxy.status == 1).all()
        if not proxies:
            print("没有可用的代理")
            task.status = 3  # 失败
            task.error_message = "没有可用的代理"
            task.end_time = datetime.now()
            db.commit()
            return

        # 解析账号cookie
        cookies = {}
        try:
            cookie_dict = json.loads(account.account_name)
            for key, value in cookie_dict.items():
                cookies[key] = value
        except:
            print("账号cookie格式错误")
            task.status = 3  # 失败
            task.error_message = "账号cookie格式错误"
            task.end_time = datetime.now()
            db.commit()
            return

        # 设置请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.zhihu.com/",
            "Connection": "keep-alive",
        }

        # 获取目标URL列表
        target_urls = get_target_urls()
        total_urls = len(target_urls)
        processed_urls = 0

        # 开始爬取
        for i, url in enumerate(target_urls):
            # 检查任务状态
            db.refresh(task)
            if task.status != 1:  # 不在运行状态
                print(f"任务 {task_id} 已停止")
                return

            # 检查URL是否已处理
            if redis.sismember("processed_urls", url):
                continue

            # 选择代理
            proxy = select_proxy(proxies)
            proxy_dict = {
                "http": f"{proxy.proxy_type.lower()}://{proxy.proxy_addr}",
                "https": f"{proxy.proxy_type.lower()}://{proxy.proxy_addr}",
            } if proxy else None

            # 发送请求
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    cookies=cookies,
                    proxies=proxy_dict,
                    timeout=settings.TIMEOUT
                )

                if response.status_code == 200:
                    # 解析页面内容
                    data = parse_page(response.text, url)

                    if data:
                        # 提取年份
                        year = extract_year(data.get("publish_time", ""))

                        # 保存数据
                        raw_data = RawData(
                            title=data.get("title"),
                            content=data.get("content"),
                            publish_time=data.get("publish_time"),
                            answer_url=url,
                            author=data.get("author"),
                            author_url=data.get("author_url"),
                            author_field=data.get("author_field"),
                            author_cert=data.get("author_cert"),
                            author_fans=data.get("author_fans"),
                            year=year,
                            task_id=task_id
                        )
                        db.add(raw_data)
                        db.commit()

                        # 标记URL已处理
                        redis.sadd("processed_urls", url)

                        processed_urls += 1

                        # 更新任务进度
                        progress = int((i + 1) / total_urls * 100)
                        task.progress = progress
                        db.commit()

                    # 请求间隔
                    time.sleep(settings.CRAWLER_DELAY)
                else:
                    print(f"请求失败，状态码: {response.status_code}, URL: {url}")

            except Exception as e:
                print(f"请求异常: {str(e)}, URL: {url}")
                # 标记代理失败
                if proxy:
                    proxy.status = 0
                    db.commit()

        # 任务完成
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
        db.close()

def get_target_urls() -> List[str]:
    """获取目标URL列表"""
    # 这里应该根据实际需求返回要爬取的URL列表
    # 示例：返回一些知乎回答URL
    urls = [
        "https://www.zhihu.com/question/12345678/answer/87654321",
        "https://www.zhihu.com/question/23456789/answer/98765432",
        # 更多URL...
    ]
    return urls

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
