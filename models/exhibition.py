"""
展会数据模型
统一的 Exhibition 数据结构，所有爬虫解析后的结果都转换为此格式。
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Exhibition:
    """单个展会/峰会/论坛的标准化数据结构"""

    name: str                           # 展会名称
    start_date: Optional[date] = None   # 开始日期
    end_date: Optional[date] = None     # 结束日期
    location: str = ""                  # 举办地点
    url: str = ""                       # 官网/报名链接
    description: str = ""               # 一句话简介
    source: str = ""                    # 数据来源（qufair / cnena / 10times / eventbrite / onezh）
    matched_keywords: list = field(default_factory=list)  # 命中的关键词列表

    def date_range_str(self) -> str:
        """返回人类可读的日期范围字符串"""
        if not self.start_date:
            return "时间待定"
        start_str = self.start_date.strftime("%m月%d日")
        if self.end_date and self.end_date != self.start_date:
            end_str = self.end_date.strftime("%m月%d日")
            return f"{start_str} - {end_str}"
        return start_str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "location": self.location,
            "url": self.url,
            "description": self.description,
            "source": self.source,
            "matched_keywords": self.matched_keywords,
        }

    def dedup_key(self) -> str:
        """生成去重用的唯一标识（名称去除空格后小写）"""
        return self.name.replace(" ", "").replace("　", "").lower().strip()
