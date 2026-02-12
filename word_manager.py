"""
单词管理器 - 管理单词库和学习进度
实现间隔重复算法（SM-2 算法）
使用数据库存储
"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from db_manager import DatabaseManager


class WordManager:
    """单词管理器 - 使用数据库存储"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()
        self._words_cache: Optional[List[Dict]] = None  # 缓存单词列表
        self._current_index: Optional[int] = None  # 缓存当前索引
    
    @property
    def words(self) -> List[Dict]:
        """获取单词列表（兼容原有接口）"""
        if self._words_cache is None:
            self._words_cache = self.db_manager.get_all_words()
        return self._words_cache
    
    @words.setter
    def words(self, value: Optional[List[Dict]]) -> None:
        """设置单词列表（兼容原有接口）"""
        self._words_cache = value
        # 同步到数据库
        if value:
            for word_data in value:
                self.db_manager.add_word(word_data['word'], word_data['meaning'])
    
    @property
    def current_index(self) -> int:
        """获取当前索引"""
        if self._current_index is None:
            self._current_index = self.db_manager.get_current_index()
        return self._current_index
    
    @current_index.setter
    def current_index(self, value: int) -> None:
        """设置当前索引"""
        self._current_index = value
        self.db_manager.set_current_index(value)
    
    def _invalidate_cache(self) -> None:
        """使缓存失效"""
        self._words_cache = None
        self._current_index = None
    
    def add_word(self, word: str, meaning: str) -> Optional[int]:
        """添加单词"""
        word_id = self.db_manager.add_word(word, meaning)
        self._invalidate_cache()
        return word_id
        
    def get_current_word(self) -> Optional[Dict]:
        """获取当前单词"""
        words = self.words
        if not words:
            return None
        
        # 确保索引在有效范围内
        if self.current_index < 0 or self.current_index >= len(words):
            self.current_index = 0
        
        if self.current_index < len(words):
            return words[self.current_index]
        return None
        
    def prev_word(self) -> None:
        """上一个单词"""
        words = self.words
        if not words:
            return
        self.current_index = (self.current_index - 1) % len(words)
        
    def next_word(self) -> None:
        """下一个单词"""
        words = self.words
        if not words:
            return
        self.current_index = (self.current_index + 1) % len(words)
    
    def delete_current_word(self) -> None:
        """删除当前单词"""
        words = self.words
        if not words:
            return
        
        if self.current_index < len(words):
            word_data = words[self.current_index]
            word_id = word_data.get('id')
            if word_id:
                self.db_manager.delete_word(word_id)
            self._invalidate_cache()
            
            # 调整索引
            if self.current_index >= len(self.words):
                self.current_index = max(0, len(self.words) - 1)
            
    def rate_word(self, quality: int) -> None:
        """
        评价单词记忆情况（简化版间隔重复算法）
        
        Args:
            quality: 1=忘记, 2=掌握
        """
        words = self.words
        if not words:
            return
        
        # 确保索引在有效范围内
        if self.current_index < 0 or self.current_index >= len(words):
            self.current_index = 0
        
        if self.current_index >= len(words):
            return
            
        word_data = words[self.current_index]
        word_id = word_data.get('id')
        if not word_id:
            return
        
        # 获取当前值
        review_count = word_data.get('review_count', 0) + 1
        ease_factor = word_data.get('ease_factor', 2.5)
        interval = word_data.get('interval', 1)
        mastered = word_data.get('mastered', False)
        
        # 简化的间隔重复算法
        if quality == 1:  # 忘记
            # 重置间隔，降低难度系数
            interval = 1
            ease_factor = max(1.3, ease_factor - 0.2)
            mastered = False
            next_review = (datetime.now() - timedelta(days=1)).isoformat()
        else:  # 掌握 (quality == 2)
            # 根据复习次数增加间隔
            if review_count == 1:
                interval = 1
            elif review_count == 2:
                interval = 3
            elif review_count == 3:
                interval = 7
            else:
                interval = int(interval * ease_factor)
            
            ease_factor = min(2.5, ease_factor + 0.15)
            
            if interval >= 30 and review_count >= 5:
                mastered = True
            
            next_review = (datetime.now() + timedelta(days=interval)).isoformat()
        
        last_review = datetime.now().isoformat()
        
        # 更新数据库
        self.db_manager.update_word(
            word_id,
            review_count=review_count,
            ease_factor=ease_factor,
            interval_days=interval,
            next_review=next_review,
            mastered=1 if mastered else 0,
            last_review=last_review
        )
        
        # 添加学习记录
        self.db_manager.add_review_record(word_id, quality)
        
        # 使缓存失效
        self._invalidate_cache()
            
    def get_words_to_review(self) -> List[Dict]:
        """获取需要复习的单词"""
        words = self.words
        now = datetime.now()
        result = []
        for w in words:
            next_review_str = w.get('next_review')
            if next_review_str:
                try:
                    next_review_dt = datetime.fromisoformat(next_review_str) if isinstance(next_review_str, str) else next_review_str
                    if next_review_dt <= now and not w.get('mastered', False):
                        result.append(w)
                except (ValueError, TypeError):
                    pass
        return result
        
    def get_new_words(self) -> List[Dict]:
        """获取新单词（未复习过的）"""
        words = self.words
        return [w for w in words if w.get('review_count', 0) == 0]
