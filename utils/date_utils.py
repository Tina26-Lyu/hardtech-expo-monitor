"""
日期工具模块
处理"下周"日期范围计算及多种日期格式解析。
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

import pytz
from dateutil import parser as dateutil_parser

from config.settings import TIMEZONE


def get_now() -> datetime:
    """获取当前时区的当前时间"""
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)


def get_next_week_range() -> Tuple[date, date]:
    """
    计算下周一到下周日的日期范围。
    返回 (next_monday, next_sunday) 两个 date 对象。
    """
    today = get_now().date()
    # 找到本周一（weekday(): 周一=0, 周日=6）
    this_monday = today - timedelta(days=today.weekday())
    next_monday = this_monday + timedelta(weeks=1)
    next_sunday = next_monday + timedelta(days=6)
    return next_monday, next_sunday


def is_in_next_week(start_date: Optional[date], end_date: Optional[date]) -> bool:
    """
    判断展会举办时间是否与"下周"有交集。
    逻辑：展会时间区间 [start, end] 与 [next_monday, next_sunday] 有重叠即为命中。
    """
    if not start_date:
        return False

    next_monday, next_sunday = get_next_week_range()

    # 如果没有结束日期，只看开始日期是否在下周
    if not end_date:
        return next_monday <= start_date <= next_sunday

    # 区间交集判断：start <= next_sunday AND end >= next_monday
    return start_date <= next_sunday and end_date >= next_monday


def parse_date_flexible(date_str: str) -> Optional[date]:
    """
    灵活解析各种日期格式字符串。
    支持：
      - "2026-07-15"
      - "2026.07.15"
      - "2026年07月15日"
      - "2026/07/15"
      - "July 15, 2026"
      - "15 Jul 2026"
    """
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    # 尝试中文格式 "2026年07月15日"
    cn_match = re.match(
        r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str
    )
    if cn_match:
        try:
            return date(int(cn_match.group(1)), int(cn_match.group(2)), int(cn_match.group(3)))
        except ValueError:
            pass

    # 尝试 dateutil 通用解析
    try:
        parsed = dateutil_parser.parse(date_str, fuzzy=True)
        return parsed.date()
    except (ValueError, dateutil_parser.ParserError, OverflowError):
        pass

    return None


def parse_date_range(range_str: str) -> Tuple[Optional[date], Optional[date]]:
    """
    解析日期范围字符串，返回 (start_date, end_date)。
    支持格式：
      - "2026-07-15 ~ 2026-07-17"
      - "2026.07.15-07.17"
      - "2026年7月15日 至 2026年7月17日"
      - "2026-07-15"（单日）
      - "07月15日 - 07月17日"（无年份，自动补当前年）
    """
    if not range_str or not range_str.strip():
        return None, None

    range_str = range_str.strip()

    # 分隔符列表
    separators = ["~", "至", "—", "–", "-", "到"]
    parts = None
    used_sep = None

    for sep in separators:
        if sep in range_str:
            parts = range_str.split(sep, 1)
            used_sep = sep
            break

    if not parts or len(parts) < 2:
        # 单日
        single = parse_date_flexible(range_str)
        return single, single

    start_str = parts[0].strip()
    end_str = parts[1].strip()

    start_date = parse_date_flexible(start_str)
    end_date = parse_date_flexible(end_str)

    # 处理 "2026.07.15-07.17" 这种省略年份的情况
    if start_date and not end_date:
        # 尝试从 start_date 补年份
        year_str = str(start_date.year)
        if re.match(r"\d{1,2}[./月]\d{1,2}", end_str):
            end_str_with_year = f"{year_str}.{end_str}"
            end_date = parse_date_flexible(end_str_with_year)
        elif re.match(r"\d{1,2}月\d{1,2}日", end_str):
            end_str_with_year = f"{year_str}年{end_str}"
            end_date = parse_date_flexible(end_str_with_year)

    return start_date, end_date


def format_next_week_range() -> str:
    """返回下周日期范围的中文描述字符串，用于推送标题"""
    next_monday, next_sunday = get_next_week_range()
    return f"{next_monday.strftime('%m月%d日')}-{next_sunday.strftime('%m月%d日')}"
