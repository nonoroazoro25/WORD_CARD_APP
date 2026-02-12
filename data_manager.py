"""
数据管理器 - 负责数据的保存和加载
"""
import json
import os
from pathlib import Path


class DataManager:
    """数据管理器"""
    
    def __init__(self, data_file='word_data.json'):
        # 数据文件路径（保存在应用目录）
        self.app_dir = Path(__file__).parent
        self.data_file = self.app_dir / data_file
        
    def save(self, data):
        """保存数据到 JSON 文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存数据失败: {e}")
            return False
            
    def load(self):
        """从 JSON 文件加载数据"""
        if not self.data_file.exists():
            return None
            
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None
            
    def backup(self):
        """备份数据文件"""
        if self.data_file.exists():
            backup_file = self.data_file.with_suffix('.json.bak')
            import shutil
            shutil.copy2(self.data_file, backup_file)
            return backup_file
        return None
