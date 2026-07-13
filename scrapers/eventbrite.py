"""
Eventbrite API 爬虫
通过 Eventbrite REST API 搜索全球科技类活动。
API 文档: https://www.eventbrite.com/platform/api
"""

import re
from typing import List

from models.exhibition import Exhibition
from scrapers.base import BaseScraper
from utils.date_utils import get_next_week_range, parse_date_flexible
from utils.logger import setup_logger
from config.settings import EVENTBRITE_API_KEY, EVENTBRITE_API_URL

logger = setup_logger("scraper.eventbrite")

# 搜索关键词列表（英文，用于 Eventbrite API 搜索）
EVENTBRITE_SEARCH_KEYWORDS = [
    "semiconductor", "AI conference", "artificial intelligence",
    "robotics", "quantum computing", "aerospace",
    "new energy", "smart manufacturing", "digital economy",
    "chip", "integrated circuit", "machine learning",
    "industrial internet", "IoT", "5G 6G",
    "embodied AI", "big model", "tech summit",
]


class EventbriteScraper(BaseScraper):
    """Eventbrite API 爬虫"""

    def __init__(self):
        super().__init__("eventbrite")

    def fetch(self) -> List[Exhibition]:
        """通过 Eventbrite API 搜索科技类活动"""
        if not EVENTBRITE_API_KEY:
            logger.warning("[eventbrite] EVENTBRITE_API_KEY 未设置，跳过此数据源")
            return []

        next_monday, next_sunday = get_next_week_range()
        # Eventbrite API 期望的日期格式：YYYY-MM-DDTHH:MM:SSZ
        start_date_str = next_monday.strftime("%Y-%m-%dT00:00:00Z")
        end_date_str = next_sunday.strftime("%Y-%m-%dT23:59:59Z")

        all_exhibitions = []

        for keyword in EVENTBRITE_SEARCH_KEYWORDS:
            logger.info(f"[eventbrite] 搜索关键词: {keyword}")

            params = {
                "q": keyword,
                "start_date.range_start": start_date_str,
                "start_date.range_end": end_date_str,
                "expand": "venue,organizer",
                "sort_by": "date",
                "page_size": 50,
            }

            headers = {
                "Authorization": f"Bearer {EVENTBRITE_API_KEY}",
                "Content-Type": "application/json",
            }

            resp = self._request(
                f"{EVENTBRITE_API_URL}events/search/",
                method="GET",
                headers=headers,
                params=params,
            )

            if not resp:
                logger.warning(f"[eventbrite] 关键词 '{keyword}' 请求失败")
                continue

            try:
                data = resp.json()
                events = data.get("events", [])
                logger.info(f"[eventbrite] 关键词 '{keyword}' 返回 {len(events)} 条结果")

                for event in events:
                    expo = self._parse_event(event)
                    if expo and expo.name:
                        all_exhibitions.append(expo)

            except (ValueError, KeyError) as e:
                logger.error(f"[eventbrite] 解析 API 响应失败: {e}")
                continue

        logger.info(f"[eventbrite] 总计抓取 {len(all_exhibitions)} 条展会记录")
        return all_exhibitions

    def _parse_event(self, event: dict) -> Exhibition:
        """解析单条 Eventbrite 事件 JSON"""
        name = event.get("name", {}).get("text", "") if isinstance(event.get("name"), dict) else str(event.get("name", ""))

        # 解析日期
        start_str = event.get("start", {}).get("utc", "") if isinstance(event.get("start"), dict) else ""
        end_str = event.get("end", {}).get("utc", "") if isinstance(event.get("end"), dict) else ""

        start_date = parse_date_flexible(start_str[:10]) if start_str else None
        end_date = parse_date_flexible(end_str[:10]) if end_str else None

        # 解析地点
        venue = event.get("venue") or {}
        if isinstance(venue, dict):
            address = venue.get("address", {})
            city = address.get("city", "") if isinstance(address, dict) else ""
            country = address.get("country_name", "") if isinstance(address, dict) else ""
            location_parts = [p for p in [city, country] if p]
            location = ", ".join(location_parts)
        else:
            location = ""

        # 提取描述（去除 HTML 标签，截取前 200 字符）
        desc_html = event.get("description", {})
        if isinstance(desc_html, dict):
            desc_text = desc_html.get("text", "")
        else:
            desc_text = str(desc_html)
        description = re.sub(r"<[^>]+>", "", desc_text)[:200] if desc_text else ""

        url = event.get("url", "")

        return Exhibition(
            name=name,
            start_date=start_date,
            end_date=end_date,
            location=location,
            url=url,
            description=description,
            source="eventbrite",
        )
