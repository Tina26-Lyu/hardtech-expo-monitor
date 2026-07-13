"""
10times.com / biztradeshows.com 爬虫
抓取全球科技类展会信息（IT & Technology / Electric & Electronics 等分类）。
"""

import re
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models.exhibition import Exhibition
from scrapers.base import BaseScraper
from utils.date_utils import parse_date_range
from utils.logger import setup_logger

logger = setup_logger("scraper.10times")

BASE_URL = "https://10times.com"

# 10times 科技相关分类页面
TENTIMES_CATEGORY_URLS = [
    "https://10times.com/technology",          # IT & Technology
    "https://10times.com/electronics-electricals",  # Electric & Electronics
    "https://10times.com/engineering",          # Industrial Engineering
    "https://10times.com/power-energy",         # Power & Energy
]


class TenTimesScraper(BaseScraper):
    """10times.com 爬虫"""

    def __init__(self):
        super().__init__("10times")

    def fetch(self) -> List[Exhibition]:
        """从 10times.com 抓取展会信息"""
        all_exhibitions = []

        for url in TENTIMES_CATEGORY_URLS:
            logger.info(f"[10times] 正在抓取: {url}")
            soup = self._get_soup(url)
            if not soup:
                continue

            exhibitions = self._parse_list_page(soup, url)
            all_exhibitions.extend(exhibitions)
            logger.info(f"[10times] 从 {url} 解析到 {len(exhibitions)} 条展会记录")

        logger.info(f"[10times] 总计抓取 {len(all_exhibitions)} 条展会记录")
        return all_exhibitions

    def _parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Exhibition]:
        """解析 10times 列表页"""
        exhibitions = []

        # 10times 页面结构：事件通常以列表/卡片形式展示
        items = (
            soup.select("div.event-box")
            or soup.select("div.card")
            or soup.select("li.event")
            or soup.select("div.listing-item")
            or soup.select("table tr")
        )

        for item in items:
            try:
                expo = self._parse_item(item, page_url)
                if expo and expo.name and len(expo.name) > 3:
                    exhibitions.append(expo)
            except Exception as e:
                logger.debug(f"[10times] 解析单条记录失败: {e}")
                continue

        return exhibitions

    def _parse_item(self, item, page_url: str) -> Exhibition:
        """解析单条展会记录"""
        # 提取名称和链接
        name_elem = item.select_one("a[href]")
        name = name_elem.get_text(strip=True) if name_elem else ""
        url = ""
        if name_elem and name_elem.get("href"):
            url = urljoin(BASE_URL, name_elem["href"])

        text = item.get_text(separator=" ", strip=True)

        # 提取时间（10times 通常使用 "Thu, 14 - Sat, 16 May 2026" 格式）
        date_str = ""
        date_patterns = [
            r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[,\s]+(\d{1,2}\s*[-–—]\s*\d{1,2}\s+\w+\s+\d{4})",
            r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[,\s]+(\d{1,2}\s+\w+\s+\d{4})",
            r"(\d{1,2}\s*[-–—]\s*\d{1,2}\s+\w+\s+\d{4})",
            r"(\d{1,2}\s+\w+\s+\d{4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group()
                break

        start_date, end_date = parse_date_range(date_str) if date_str else (None, None)

        # 提取地点
        location = ""
        loc_patterns = [
            r"([\u4e00-\u9fa5]{2,6},\s*[\u4e00-\u9fa5]+)",  # 中文格式 "上海, 中国"
            r"([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)",       # 英文格式 "New York, USA"
            r"([\u4e00-\u9fa5]{2,8}(?:国际)?会展中心)",
        ]
        for pattern in loc_patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group()
                break

        return Exhibition(
            name=name,
            start_date=start_date,
            end_date=end_date,
            location=location,
            url=url,
            description="",
            source="10times",
        )
