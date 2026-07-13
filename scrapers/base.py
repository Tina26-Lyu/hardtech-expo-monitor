"""
爬虫基类模块
提供统一的 HTTP 请求封装、重试机制、User-Agent 轮换、HTML 解析等通用功能。
所有具体数据源爬虫继承此基类，只需实现 parse() 方法。
"""

import random
import time
from abc import ABC, abstractmethod
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from config.settings import REQUEST_DELAY, REQUEST_RETRY, REQUEST_TIMEOUT, USER_AGENTS
from models.exhibition import Exhibition
from utils.logger import setup_logger

logger = setup_logger("scraper.base")


class BaseScraper(ABC):
    """所有爬虫的抽象基类"""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()

    def _get_headers(self) -> dict:
        """返回带随机 User-Agent 的请求头"""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }

    def _request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """
        带重试机制的 HTTP 请求封装。
        每次重试自动轮换 User-Agent，并在请求间加入延迟。
        """
        for attempt in range(1, REQUEST_RETRY + 1):
            try:
                kwargs.setdefault("headers", self._get_headers())
                kwargs.setdefault("timeout", REQUEST_TIMEOUT)

                if method.upper() == "GET":
                    resp = self.session.get(url, **kwargs)
                else:
                    resp = self.session.post(url, **kwargs)

                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"

                # 请求间延迟
                if REQUEST_DELAY > 0:
                    time.sleep(REQUEST_DELAY)

                return resp

            except requests.RequestException as e:
                logger.warning(
                    f"[{self.source_name}] 请求失败 (第{attempt}/{REQUEST_RETRY}次): {url} - {e}"
                )
                if attempt < REQUEST_RETRY:
                    time.sleep(REQUEST_DELAY * attempt)  # 递增延迟
                else:
                    logger.error(f"[{self.source_name}] 请求最终失败，放弃: {url}")
                    return None

        return None

    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """获取页面并返回 BeautifulSoup 对象"""
        resp = self._request(url)
        if not resp:
            return None
        return BeautifulSoup(resp.text, "lxml")

    @abstractmethod
    def fetch(self) -> List[Exhibition]:
        """
        抓取数据，返回 Exhibition 列表。
        子类必须实现此方法。
        """
        pass
