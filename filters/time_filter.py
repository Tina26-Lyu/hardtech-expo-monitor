"""
时间筛选与去重模块
1. 时间过滤：只保留举办时间在"下周（下周一至下周日）"范围内的展会
2. 去重：不同数据源可能抓取到同一条展会，按名称去重
"""

from datetime import date
from typing import List

from models.exhibition import Exhibition
from utils.date_utils import is_in_next_week
from utils.logger import setup_logger

logger = setup_logger("filter.time")


def filter_by_time(exhibitions: List[Exhibition]) -> List[Exhibition]:
    """
    时间过滤：只保留举办时间与"下周"有交集的展会。
    """
    filtered = []

    for expo in exhibitions:
        if is_in_next_week(expo.start_date, expo.end_date):
            filtered.append(expo)

    logger.info(
        f"时间筛选: 输入 {len(exhibitions)} 条 → 命中 {len(filtered)} 条"
    )
    return filtered


def deduplicate(exhibitions: List[Exhibition]) -> List[Exhibition]:
    """
    去重：按展会名称（去空格小写后）去重。
    当多个数据源返回同一条展会时，优先保留信息更完整的那条。
    """
    seen = {}
    for expo in exhibitions:
        key = expo.dedup_key()
        if key not in seen:
            seen[key] = expo
        else:
            # 保留信息更完整的那条
            existing = seen[key]
            existing_score = _completeness_score(existing)
            new_score = _completeness_score(expo)
            if new_score > existing_score:
                # 合并信息（取两者中非空的部分）
                if not existing.url and expo.url:
                    existing.url = expo.url
                if not existing.description and expo.description:
                    existing.description = expo.description
                if not existing.location and expo.location:
                    existing.location = expo.location
                if not existing.start_date and expo.start_date:
                    existing.start_date = expo.start_date
                if not existing.end_date and expo.end_date:
                    existing.end_date = expo.end_date
                # 合并关键词
                for kw in expo.matched_keywords:
                    if kw not in existing.matched_keywords:
                        existing.matched_keywords.append(kw)
                seen[key] = expo

    result = list(seen.values())
    logger.info(
        f"去重: 输入 {len(exhibitions)} 条 → 输出 {len(result)} 条"
    )
    return result


def _completeness_score(expo: Exhibition) -> int:
    """计算展会信息的完整度评分，分越高信息越完整"""
    score = 0
    if expo.name:
        score += 1
    if expo.start_date:
        score += 1
    if expo.end_date:
        score += 1
    if expo.location:
        score += 1
    if expo.url:
        score += 1
    if expo.description:
        score += 1
    return score


def sort_by_date(exhibitions: List[Exhibition]) -> List[Exhibition]:
    """按开始日期排序，无日期的排在最后"""
    return sorted(
        exhibitions,
        key=lambda e: (e.start_date is None, e.start_date or date.max),
    )
