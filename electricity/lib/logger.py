"""日志系统 — 统一 logging 配置，输出到日志文件与控制台"""

import logging
import os
from logging.handlers import RotatingFileHandler

# 日志目录与文件
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")

# 格式化：时间 级别 模块 信息
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# 全局入口使用的日志器名
_ROOT_NAME = "electricity"
_logger = None


def get_logger(name=_ROOT_NAME):
    """获取应用日志器；未配置时自动初始化。"""
    global _logger
    if _logger is None:
        _logger = setup_logger(name)
    return _logger


def setup_logger(name=_ROOT_NAME, level=logging.INFO):
    """配置并返回应用日志器。

    - 输出到 data/app.log（按 1MB 轮转，保留 3 份）
    - 同时输出到控制台
    - 幂等：重复调用不会重复添加 handler
    """
    logger = logging.getLogger(name)
    if logger.handlers:  # 已配置过，避免重复
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(_FORMAT)

    # 文件 handler（轮转）
    os.makedirs(_LOG_DIR, exist_ok=True)
    file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台 handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger