"""
第一展会网 (onezh.com) 爬虫
抓取全国展会排期信息。
"""

import re
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models.exhibition import Exhibition
from scrapers.base import BaseScraper
from utils.date_utils import get_now, parse_date_range
from utils.logger import setup_logger

logger = setup_logger("scraper.onezh")

BASE_URL = "https://www.onezh.com"


class OnezhScraper(BaseScraper):
    """第一展会网爬虫"""

    def __init__(self):
        super().__init__("onezh")

    def fetch(self) -> List[Exhibition]:
        """从第一展会网抓取展会信息"""
        now = get_now()
        all_exhibitions = []

        # 抓取当年和下一年的展会排期
        for year in [now.year, now.year + 1]:
            for month in range(1, 13):
                # 只抓取当前月及之后的月份
                if year == now.year and month < now.month:
                    continue

                url = f"{BASE_URL}/zhanhui/1_0_0_0_{year}{month:02d}01/{year}{month:02d}28/"
                logger.info(f"[onezh] 正在抓取: {url}")

                soup = self._get_soup(url)
                if not soup:
                    continue

                exhibitions = self._parse_list_page(soup, url)
                all_exhibitions.extend(exhibitions)
                logger.info(f"[onezh] 从 {url} 解析到 {len(exhibitions)} 条展会记录")

                # 限制抓取范围：只抓到下下月
                if year == now.year and month >= now.month + 2:
                    break
            if year == now.year and now.month + 2 > 12:
                continue

        logger.info(f"[onezh] 总计抓取 {len(all_exhibitions)} 条展会记录")
        return all_exhibitions

    def _parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Exhibition]:
        """解析第一展会网列表页"""
        exhibitions = []

        # 第一展会网展会列表结构
        items = (
            soup.select("ul li")
            or soup.select("table tr")
            or soup.select(".zhanhui-list li")
            or soup.select(".list-item")
            or soup.select(".expo-item")
        )

        for item in items:
            try:
                expo = self._parse_item(item, page_url)
                if expo and expo.name and len(expo.name) > 2:
                    exhibitions.append(expo)
            except Exception as e:
                logger.debug(f"[onezh] 解析单条记录失败: {e}")
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
            r"\d{4}年\d{1,2}月\d{1,2}日\s*(?:---|-|至|~)\s*\d{1,2}月\d{1,2}日",
            r"\d{4}年\d{1,2}月\d{1,2}日",
            r"\d{4}[\.\-/]\d{1,2}[\.\-/]\d{1,2}",
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
            r"([\u4e00-\u9fa5]{2,4}(?:市|省))",
            r"地区[：:]\s*([\u4e00-\u9fa5]{2,6})",
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
            source="onezh",
        )
