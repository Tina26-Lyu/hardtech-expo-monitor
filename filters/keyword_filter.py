"""
关键词筛选模块
根据领域关键词列表，对展会名称和简介进行匹配。
命中任意关键词即保留该展会，并记录命中的关键词列表。
"""

from typing import List

from config.settings import ALL_KEYWORDS, KEYWORD_GROUPS
from models.exhibition import Exhibition
from utils.logger import setup_logger

logger = setup_logger("filter.keyword")


def filter_by_keywords(exhibitions: List[Exhibition]) -> List[Exhibition]:
    """
    对展会列表进行关键词筛选。
    展会名称或简介中命中任意关键词即保留。
    返回命中关键词的展会列表，并在每条记录中记录命中的关键词。
    """
    matched = []

    for expo in exhibitions:
        # 合并名称和简介作为匹配文本
        text = f"{expo.name} {expo.description}".lower()

        hit_keywords = []
        for keyword in ALL_KEYWORDS:
            if keyword.lower() in text:
                hit_keywords.append(keyword)

        if hit_keywords:
            expo.matched_keywords = hit_keywords
            matched.append(expo)

    logger.info(
        f"关键词筛选: 输入 {len(exhibitions)} 条 → 命中 {len(matched)} 条"
    )
    return matched


def get_keyword_category(expo: Exhibition) -> str:
    """
    根据命中的关键词，返回所属领域大类名称。
    如果命中多个大类，返回第一个匹配的大类。
    """
    text = f"{expo.name} {expo.description}".lower()

    for category, keywords in KEYWORD_GROUPS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category

    return "其他"
