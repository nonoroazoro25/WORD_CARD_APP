#!/usr/bin/env python3
"""
英语单词卡片应用 - 主程序
基于 PyQt5 开发，支持间隔重复算法
"""
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from main_window import MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('word_card_app.log', encoding='utf-8'),
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
