
import re
from datetime import datetime
from typing import Optional

def extract_year(date_str: str) -> int:
    """从日期字符串中提取年份"""
    if not date_str:
        return datetime.now().year

    # 尝试匹配YYYY-MM-DD格式
    match = re.search(r"(\d{4})-\d{2}-\d{2}", date_str)
    if match:
        return int(match.group(1))

    # 尝试匹配YYYY年MM月DD日格式
    match = re.search(r"(\d{4})年", date_str)
    if match:
        return int(match.group(1))

    # 默认返回当前年份
    return datetime.now().year

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.2f} {size_names[i]}"

def safe_filename(filename: str) -> str:
    """生成安全的文件名"""
    # 移除或替换不安全的字符
    safe_chars = re.sub(r'[\/*?:"<>|]', "", filename)
    # 替换空格为下划线
    safe_chars = re.sub(r'\s+', '_', safe_chars)
    # 限制长度
    if len(safe_chars) > 200:
        safe_chars = safe_chars[:200]

    return safe_chars

def get_status_text(status: int) -> str:
    """获取任务状态文本"""
    status_map = {
        0: "等待",
        1: "运行",
        2: "暂停",
        3: "失败",
        4: "完成"
    }
    return status_map.get(status, "未知")

def get_status_class(status: int) -> str:
    """获取任务状态样式类"""
    status_map = {
        0: "status-waiting",
        1: "status-running",
        2: "status-paused",
        3: "status-failed",
        4: "status-completed"
    }
    return status_map.get(status, "")
