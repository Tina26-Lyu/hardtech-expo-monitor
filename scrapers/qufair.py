"""
去展网 (qufair.com) 爬虫
抓取半导体、人工智能、电子信息等相关行业的展会列表。
"""

import re
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models.exhibition import Exhibition
from scrapers.base import BaseScraper
from utils.date_utils import parse_date_range
from utils.logger import setup_logger

logger = setup_logger("scraper.qufair")

# 去展网相关行业分类页面（半导体/电子/信息技术/通信/新能源等）
QUFAIR_CATEGORY_URLS = [
    # 半导体相关
    "https://www.qufair.com/fl/262-273-{year}/",   # 半导体展会
    # 电子信息相关
    "https://www.qufair.com/fl/262-{year}/",       # 电子展会
    # 信息技术相关
    "https://www.qufair.com/fl/299-{year}/",       # 信息技术展会
    # 通信相关
    "https://www.qufair.com/fl/300-{year}/",       # 通信展会
    # 工业相关
    "https://www.qufair.com/fl/258-{year}/",       # 工业展会
]

BASE_URL = "https://www.qufair.com"


class QufairScraper(BaseScraper):
    """去展网爬虫"""

    def __init__(self):
        super().__init__("qufair")

    def fetch(self) -> List[Exhibition]:
        """从去展网抓取展会信息"""
        from utils.date_utils import get_now
        year = get_now().year

        all_exhibitions = []

        for url_template in QUFAIR_CATEGORY_URLS:
            url = url_template.format(year=year)
            logger.info(f"[qufair] 正在抓取: {url}")
            soup = self._get_soup(url)
            if not soup:
                continue

            exhibitions = self._parse_list_page(soup, url)
            all_exhibitions.extend(exhibitions)
            logger.info(f"[qufair] 从 {url} 解析到 {len(exhibitions)} 条展会记录")

        # 同时抓取下一年度的展会（年底时下周可能跨年）
        next_year = year + 1
        for url_template in QUFAIR_CATEGORY_URLS:
            url = url_template.format(year=next_year)
            logger.info(f"[qufair] 正在抓取(下一年): {url}")
            soup = self._get_soup(url)
            if not soup:
                continue
            exhibitions = self._parse_list_page(soup, url)
            all_exhibitions.extend(exhibitions)
            logger.info(f"[qufair] 从 {url} 解析到 {len(exhibitions)} 条展会记录")

        logger.info(f"[qufair] 总计抓取 {len(all_exhibitions)} 条展会记录")
        return all_exhibitions

    def _parse_list_page(self, soup: BeautifulSoup, page_url: str) -> List[Exhibition]:
        """解析去展网列表页，提取展会信息"""
        exhibitions = []

        # 去展网列表页通常使用表格或列表结构展示展会
        # 尝试多种可能的 CSS 选择器以适应页面结构变化
        items = (
            soup.select("ul.list li")
            or soup.select("div.expo-list li")
            or soup.select("table tr")
            or soup.select(".zhanhui-list li")
            or soup.select(".list-item")
        )

        for item in items:
            try:
                expo = self._parse_item(item, page_url)
                if expo and expo.name:
                    exhibitions.append(expo)
            except Exception as e:
                logger.debug(f"[qufair] 解析单条记录失败: {e}")
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

        # 提取文本内容用于解析时间和地点
        text = item.get_text(separator=" ", strip=True)

        # 提取时间（尝试匹配各种日期格式）
        date_str = ""
        time_patterns = [
            r"\d{4}[\.\-/年]\d{1,2}[\.\-/月]\d{1,2}[日]?[^~\-—至]*(?:~|至|-|—|–)\s*\d{1,2}[\.\-/月]\d{1,2}[日]?",
            r"\d{4}[\.\-/年]\d{1,2}[\.\-/月]\d{1,2}[日]?",
            r"\d{4}\.\d{1,2}\.\d{1,2}\s*~\s*\d{1,2}\.\d{1,2}",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group()
                break

        start_date, end_date = parse_date_range(date_str) if date_str else (None, None)

        # 提取地点（通常包含"中国"+"城市名"或"XX会展中心"）
        location = ""
        loc_patterns = [
            r"中国[·\-]?\s*([\u4e00-\u9fa5]{2,6})",
            r"([\u4e00-\u9fa5]{2,8}(?:国际)?会展中心)",
            r"([\u4e00-\u9fa5]{2,4}(?:市|省))",
        ]
        for pattern in loc_patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group()
                break

        # 提取简介
        desc_elem = item.select_one(".desc, .intro, .summary, p")
        description = desc_elem.get_text(strip=True) if desc_elem else ""

        return Exhibition(
            name=name,
            start_date=start_date,
            end_date=end_date,
            location=location,
            url=url,
            description=description[:200] if description else "",
            source="qufair",
        )
