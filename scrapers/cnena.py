"""
CNENA 会展门户 (cnena.com) 爬虫
抓取按时间排期的展会信息列表。
"""

import re
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models.exhibition import Exhibition
from scrapers.base import BaseScraper
from utils.date_utils import get_now, parse_date_range
from utils.logger import setup_logger

logger = setup_logger("scraper.cnena")

BASE_URL = "http://www.cnena.com"


class CnenaScraper(BaseScraper):
    """CNENA 会展门户爬虫"""

    def __init__(self):
        super().__init__("cnena")

    def fetch(self) -> List[Exhibition]:
        """从 CNENA 抓取展会信息"""
        now = get_now()
        all_exhibitions = []

        # 抓取当月和下月的展会排期
        for month_offset in [0, 1, 2]:
            target_date = now.replace(day=1)
            if month_offset > 0:
                # 计算目标月份
                year = target_date.year
                month = target_date.month + month_offset
                if month > 12:
                    year += 1
                    month -= 12
                target_date = target_date.replace(year=year, month=month)

            daytime = target_date.strftime("%Y-%m-%d")
            url = f"{BASE_URL}/showroom/list_time.php?daytime={daytime}"
            logger.info(f"[cnena] 正在抓取: {url}")

            soup = self._get_soup(url)
            if not soup:
                continue

            exhibitions = self._parse_list_page(soup, url)
            all_exhibitions.extend(exhibitions)
            logger.info(f"[cnena] 从 {url} 解析到 {len(exhibitions)} 条展会记录")

        logger.info(f"[cnena] 总计抓取 {len(all_exhibitions)} 条展会记录")
        return all_exhibitions

    def _parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Exhibition]:
        """解析 CNENA 列表页"""
        exhibitions = []

        # CNENA 展会列表通常使用表格或列表结构
        items = (
            soup.select("ul li")
            or soup.select("table tr")
            or soup.select(".show_list li")
            or soup.select(".list li")
            or soup.select(".expo-item")
        )

        for item in items:
            try:
                expo = self._parse_item(item, page_url)
                if expo and expo.name and len(expo.name) > 2:
                    exhibitions.append(expo)
            except Exception as e:
                logger.debug(f"[cnena] 解析单条记录失败: {e}")
                continue

        return exhibitions

    def _parse_item(self, item, page_url: str) -> Exhibition:
        """解析单条展会记录"""
        # 提取名称和链接
        name_elem = item.select_one("a")
        name = name_elem.get_text(strip=True) if name_elem else ""
        url = ""
        if name_elem and name_elem.get("href"):
            url = urljoin(BASE_URL, name_elem["href"])

        text = item.get_text(separator=" ", strip=True)

        # 提取时间
        date_str = ""
        time_patterns = [
            r"\d{4}[\.\-/年]\d{1,2}[\.\-/月]\d{1,2}[日]?\s*(?:~|至|-|—|–)\s*\d{4}[\.\-/年]?\d{1,2}[\.\-/月]\d{1,2}[日]?",
            r"\d{4}[\.\-/年]\d{1,2}[\.\-/月]\d{1,2}[日]?",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group()
                break

        start_date, end_date = parse_date_range(date_str) if date_str else (None, None)

        # 提取地点
        location = ""
        loc_patterns = [
            r"([\u4e00-\u9fa5]{2,8}(?:国际)?会展中心)",
            r"([\u4e00-\u9fa5]{2,4}(?:市|省)[\u4e00-\u9fa5]*)",
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
            source="cnena",
        )
