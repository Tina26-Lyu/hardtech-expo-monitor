"""
微信推送模块
支持 PushPlus 和 Server酱 两种推送渠道。
将筛选后的展会信息格式化为 Markdown 消息，推送到微信。
"""

from typing import List

import requests

from config.settings import (
    PUSHPLUS_TOKEN,
    PUSHPLUS_URL,
    PUSH_METHOD,
    SERVERCHAN_KEY,
    SERVERCHAN_URL,
)
from filters.keyword_filter import get_keyword_category
from models.exhibition import Exhibition
from utils.date_utils import format_next_week_range, get_now
from utils.logger import setup_logger

logger = setup_logger("notify.wechat")


def format_message(exhibitions: List[Exhibition]) -> tuple:
    """
    将展会列表格式化为推送消息。
    返回 (title, content) 元组。
    """
    next_week_str = format_next_week_range()
    today_str = get_now().strftime("%Y-%m-%d")

    if not exhibitions:
        title = f"硬科技展会监控 | 下周({next_week_str})暂无相关展会"
        content = f"## 硬科技展会监控报告\n\n"
        content += f"**报告日期**: {today_str}\n"
        content += f"**监控范围**: 下周({next_week_str})\n\n"
        content += "---\n\n"
        content += f"下周暂无符合条件的硬科技展会。\n\n"
        content += f"*监控领域: 半导体、人工智能、硬科技、先进制造、数字经济*\n"
        return title, content

    title = f"硬科技展会监控 | 下周({next_week_str})共{len(exhibitions)}场展会"

    content = f"## 硬科技展会监控报告\n\n"
    content += f"**报告日期**: {today_str}\n"
    content += f"**监控范围**: 下周({next_week_str})\n"
    content += f"**符合条件的展会**: {len(exhibitions)} 场\n\n"
    content += "---\n\n"

    for i, expo in enumerate(exhibitions, 1):
        category = get_keyword_category(expo)
        content += f"### {i}. {expo.name}\n\n"
        content += f"| 字段 | 信息 |\n"
        content += f"|---|---|\n"
        content += f"| 领域 | {category} |\n"
        content += f"| 时间 | {expo.date_range_str()} |\n"
        if expo.location:
            content += f"| 地点 | {expo.location} |\n"
        if expo.url:
            content += f"| 链接 | [点击查看]({expo.url}) |\n"
        if expo.matched_keywords:
            content += f"| 关键词 | {', '.join(expo.matched_keywords[:5])} |\n"
        content += f"| 来源 | {expo.source} |\n"
        content += "\n"

        if expo.description:
            content += f"> {expo.description}\n\n"

        content += "---\n\n"

    content += f"\n*数据来源: 去展网、CNENA会展门户、10times、Eventbrite、第一展会网*\n"
    content += f"*自动监控 by 硬科技展会监控系统*\n"

    return title, content


def send_via_pushplus(title: str, content: str) -> bool:
    """通过 PushPlus 推送消息到微信"""
    if not PUSHPLUS_TOKEN:
        logger.error("[pushplus] PUSHPLUS_TOKEN 未设置，无法推送")
        return False

    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "markdown",
    }

    try:
        resp = requests.post(PUSHPLUS_URL, json=payload, timeout=15)
        result = resp.json()
        if result.get("code") == 200:
            logger.info(f"[pushplus] 推送成功: {result.get('msg')}")
            return True
        else:
            logger.error(f"[pushplus] 推送失败: {result.get('msg')}")
            return False
    except Exception as e:
        logger.error(f"[pushplus] 推送异常: {e}")
        return False


def send_via_serverchan(title: str, content: str) -> bool:
    """通过 Server酱 推送消息到微信"""
    if not SERVERCHAN_KEY:
        logger.error("[serverchan] SERVERCHAN_KEY 未设置，无法推送")
        return False

    url = SERVERCHAN_URL.format(key=SERVERCHAN_KEY)
    payload = {
        "title": title[:32],  # Server酱标题限制32字
        "desp": content,
    }

    try:
        resp = requests.post(url, data=payload, timeout=15)
        result = resp.json()
        if result.get("code") == 0:
            logger.info(f"[serverchan] 推送成功: {result.get('msg')}")
            return True
        else:
            logger.error(f"[serverchan] 推送失败: {result.get('msg')}")
            return False
    except Exception as e:
        logger.error(f"[serverchan] 推送异常: {e}")
        return False


def push_exhibitions(exhibitions: List[Exhibition]) -> bool:
    """
    格式化展会信息并推送到微信。
    根据 PUSH_METHOD 环境变量选择推送渠道。
    返回推送是否成功。
    """
    title, content = format_message(exhibitions)

    logger.info(f"准备推送: {title}")
    logger.debug(f"推送内容预览:\n{content[:500]}...")

    if PUSH_METHOD == "serverchan":
        return send_via_serverchan(title, content)
    else:
        return send_via_pushplus(title, content)
