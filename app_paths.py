"""
应用路径 - 统一的数据目录
无论开发环境还是打包后的应用，都使用同一个固定的数据目录，
保证始终读取同一份数据库文件。
"""
from pathlib import Path


def get_app_data_dir() -> Path:
    """返回应用数据目录（数据库、配置等持久化文件存放位置）
    
    统一使用用户目录下的 Application Support，确保：
    - 开发时和打包后读取同一份数据库
    - 无论应用在哪里运行，都使用固定位置
    - 符合 macOS 应用数据存储的最佳实践
    """
    base = Path.home() / "Library" / "Application Support" / "单词卡片"
    base.mkdir(parents=True, exist_ok=True)
    return base
