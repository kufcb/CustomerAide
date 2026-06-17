# Python 日志模块
import logging
import os
from logging.handlers import TimedRotatingFileHandler

# 日志文件路径（与当前脚本同目录）
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "logs.log")

# 使用具名 logger，避免污染根 logger
logger = logging.getLogger("CustomerAide")
logger.setLevel(logging.INFO)

# 防止重复添加 handler（热重载时可能重复初始化）
if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 控制台输出 handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 按天滚动文件 handler，保留 30 天日志
    fh = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",   # 每天午夜切割日志文件
        interval=1,        # 间隔 1 天
        backupCount=30,    # 保留最近 30 个日志文件
        encoding="utf-8",
    )
    fh.suffix = "%Y-%m-%d"  # 日志文件后缀格式：logs.log.2026-01-01
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def get_logger() -> logging.Logger:
    """获取已配置好的 CustomerAide logger 实例"""
    return logger


__all__ = ["get_logger", "logger"]
