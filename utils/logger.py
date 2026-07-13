"""
日志配置模块
统一的日志格式，同时输出到控制台和文件。
"""

import logging
import sys


def setup_logger(name: str = "expo_monitor", level: int = logging.INFO) -> logging.Logger:
    """创建并返回配置好的 logger 实例"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
