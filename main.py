"""
硬科技展会监控自动化系统 - 主程序入口
=====================================
功能流程：
  1. 从多个数据源抓取展会信息
  2. 关键词筛选（半导体/AI/硬科技/先进制造/数字经济）
  3. 时间筛选（只保留下周举办的展会）
  4. 多源去重
  5. 格式化并推送到微信

使用方式：
  本地运行:  python main.py
  GitHub Actions: 每天北京时间 08:00 自动触发
"""

import sys
import time
from typing import List

from config.settings import ENABLED_SOURCES
from filters.keyword_filter import filter_by_keywords
from filters.time_filter import deduplicate, filter_by_time, sort_by_date
from models.exhibition import Exhibition
from notify.wechat_push import push_exhibitions
from utils.date_utils import format_next_week_range, get_now
from utils.logger import setup_logger

logger = setup_logger("main")


def run_scrapers() -> List[Exhibition]:
    """运行所有启用的数据源爬虫，汇总返回展会列表"""
    all_exhibitions = []

    # 动态导入各爬虫模块，按配置启用
    scraper_map = {
        "qufair": ("scrapers.qufair", "QufairScraper"),
        "cnena": ("scrapers.cnena", "CnenaScraper"),
        "ten_times": ("scrapers.ten_times", "TenTimesScraper"),
        "eventbrite": ("scrapers.eventbrite", "EventbriteScraper"),
        "onezh": ("scrapers.onezh", "OnezhScraper"),
    }

    for source_name, (module_path, class_name) in scraper_map.items():
        if not ENABLED_SOURCES.get(source_name, False):
            logger.info(f"数据源 [{source_name}] 已禁用，跳过")
            continue

        try:
            logger.info(f"========== 开始抓取数据源: {source_name} ==========")
            # 动态导入模块和类
            import importlib
            module = importlib.import_module(module_path)
            scraper_class = getattr(module, class_name)
            scraper = scraper_class()

            exhibitions = scraper.fetch()
            all_exhibitions.extend(exhibitions)
            logger.info(f"[{source_name}] 返回 {len(exhibitions)} 条展会记录")

        except Exception as e:
            logger.error(f"数据源 [{source_name}] 抓取失败: {e}", exc_info=True)
            continue

    logger.info(f"========== 所有数据源抓取完成，共 {len(all_exhibitions)} 条 ==========")
    return all_exhibitions


def main():
    """主执行流程"""
    start_time = time.time()

    now = get_now()
    next_week = format_next_week_range()
    logger.info("=" * 60)
    logger.info(f"硬科技展会监控自动化系统启动")
    logger.info(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"监控范围: 下周({next_week})")
    logger.info("=" * 60)

    # Step 1: 抓取数据
    logger.info(">>> Step 1/5: 抓取展会数据")
    all_exhibitions = run_scrapers()

    if not all_exhibitions:
        logger.warning("未抓取到任何展会数据，将推送空结果通知")
        push_exhibitions([])
        return

    # Step 2: 关键词筛选
    logger.info(">>> Step 2/5: 关键词筛选")
    keyword_matched = filter_by_keywords(all_exhibitions)

    if not keyword_matched:
        logger.info("关键词筛选后无匹配展会，将推送空结果通知")
        push_exhibitions([])
        return

    # Step 3: 时间筛选
    logger.info(">>> Step 3/5: 时间筛选（下周）")
    time_matched = filter_by_time(keyword_matched)

    if not time_matched:
        logger.info("时间筛选后无匹配展会，将推送空结果通知")
        push_exhibitions([])
        return

    # Step 4: 去重
    logger.info(">>> Step 4/5: 多源去重")
    deduped = deduplicate(time_matched)

    # 排序
    sorted_expos = sort_by_date(deduped)

    # Step 5: 推送
    logger.info(f">>> Step 5/5: 推送到微信 (共 {len(sorted_expos)} 条展会)")
    success = push_exhibitions(sorted_expos)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"任务完成! 耗时 {elapsed:.1f}s")
    logger.info(f"推送状态: {'成功' if success else '失败'}")
    logger.info(f"展会数量: {len(sorted_expos)} 场")
    logger.info("=" * 60)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
