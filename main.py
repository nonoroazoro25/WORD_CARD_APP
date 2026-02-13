#!/usr/bin/env python3
"""
英语单词卡片应用 - 主程序
基于 PyQt5 开发，支持间隔重复算法
"""
import sys
import logging
from PyQt5.QtWidgets import QApplication
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
    
    # 设置应用样式：护眼柔和背景，减少刺眼
    app.setStyle('Fusion')
    app.setStyleSheet("""
        QWidget { background-color: #d0d4d0; color: #2d2d2d; }
        QLabel { color: #2d2d2d; font-size: 13px; }
        QGroupBox { color: #2d2d2d; font-size: 13px; font-weight: bold; }
        QGroupBox::title { color: #2d2d2d; }
        QPushButton { color: #2d2d2d; font-size: 13px; }
        QLineEdit { color: #2d2d2d; font-size: 14px; background-color: #e2e0da; }
        QListWidget { color: #2d2d2d; font-size: 13px; background-color: #e2e0da; }
        QTextEdit { color: #2d2d2d; font-size: 13px; background-color: #e2e0da; }
        QProgressBar { color: #2d2d2d; }
    """)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
