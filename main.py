#!/usr/bin/env python3
"""
英语单词卡片应用 - 主程序
基于 PyQt5 开发，支持间隔重复算法
"""
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from app_paths import get_app_data_dir
from main_window import MainWindow

# 配置日志（打包后写入固定数据目录）
_log_dir = get_app_data_dir()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_dir / 'word_card_app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("单词卡片")
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
