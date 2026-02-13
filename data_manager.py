"""
数据管理器 - 仅用于从旧版 JSON 文件迁移数据到数据库
"""
import json
from app_paths import get_app_data_dir


class DataManager:
    """数据管理器"""
    
    def __init__(self, data_file='word_data.json'):
        # 与数据库使用同一数据目录，打包后路径固定
        self.app_dir = get_app_data_dir()
        self.data_file = self.app_dir / data_file
        
    def load(self):
        """从 JSON 文件加载数据（仅用于迁移）"""
        if not self.data_file.exists():
            return None
            
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None
