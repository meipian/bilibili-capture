#!/usr/bin/env python3
"""
Bilibili视频缩略图提取器
主入口文件
"""
import sys
import logging

# 导入配置和UI
from config import LOG_LEVEL
from ui import BilibiliCaptureUI


def setup_logging():
    """配置日志"""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bb_capture.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """主函数"""
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        import tkinter as tk
        root = tk.Tk()
        app = BilibiliCaptureUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        raise


if __name__ == "__main__":
    main()
