"""
数据库管理器 - 使用 SQLite 存储单词数据
"""
import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Iterator

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器 - 使用 SQLite"""
    
    def __init__(self, db_file='word_card.db'):
        """初始化数据库管理器"""
        # 数据库文件路径（保存在应用目录）
        self.app_dir = Path(__file__).parent
        self.db_file = self.app_dir / db_file
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        return conn
    
    @contextmanager
    def _db_connection(self) -> Iterator[sqlite3.Connection]:
        """数据库连接上下文管理器，自动处理连接关闭和错误"""
        conn = self.get_connection()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def init_database(self) -> None:
        """初始化数据库表结构"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            
            # 创建单词表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    meaning TEXT NOT NULL,
                    review_count INTEGER DEFAULT 0,
                    ease_factor REAL DEFAULT 2.5,
                    interval_days INTEGER DEFAULT 1,
                    next_review TEXT,
                    mastered INTEGER DEFAULT 0,
                    last_review TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON words(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_next_review ON words(next_review)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mastered ON words(mastered)')
            
            # 创建学习记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL,
                    review_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (word_id) REFERENCES words(id)
                )
            ''')
            
            # 创建应用状态表（存储当前索引等）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            # 初始化当前索引
            cursor.execute('''
                INSERT OR IGNORE INTO app_state (key, value) 
                VALUES ('current_index', '0')
            ''')
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def add_word(self, word: str, meaning: str) -> Optional[int]:
        """添加单词，返回单词ID"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            # 设置 next_review 为昨天，确保新添加的单词显示为红色（需要复习）
            yesterday = (now - timedelta(days=1)).isoformat()
            cursor.execute('''
                INSERT OR IGNORE INTO words 
                (word, meaning, next_review, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (word, meaning, yesterday, now.isoformat(), now.isoformat()))
            conn.commit()
            return cursor.lastrowid if cursor.rowcount > 0 else None
    
    def batch_add_words(self, words_list: List[tuple], batch_size: int = 1000) -> int:
        """
        批量添加单词（用于大量导入）
        
        Args:
            words_list: [(word, meaning), ...] 格式的列表
            batch_size: 每批处理的单词数量
            
        Returns:
            int: 成功添加的单词数量
        """
        with self._db_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            yesterday = (now - timedelta(days=1)).isoformat()
            now_str = now.isoformat()
            
            total = len(words_list)
            added = 0
            
            for i in range(0, total, batch_size):
                batch = words_list[i:i + batch_size]
                for word, meaning in batch:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO words 
                            (word, meaning, next_review, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (word, meaning, yesterday, now_str, now_str))
                        if cursor.rowcount > 0:
                            added += 1
                    except Exception as e:
                        logger.warning(f"跳过单词 {word}: {e}")
                
                conn.commit()
                if (i + batch_size) % 5000 == 0:
                    logger.info(f"已处理 {min(i + batch_size, total)}/{total} 个单词...")
            
            logger.info(f"批量添加完成，成功添加 {added}/{total} 个单词")
            return added
    
    def get_word_count(self) -> int:
        """快速获取单词总数（不加载数据）"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM words')
            return cursor.fetchone()[0]
    
    def clear_all_words(self) -> None:
        """清空单词库：删除所有单词、学习记录，并重置当前索引"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM review_history')
            cursor.execute('DELETE FROM words')
            cursor.execute(
                "INSERT OR REPLACE INTO app_state (key, value) VALUES ('current_index', '0')"
            )
            conn.commit()
            logger.info("已清空单词库")
    
    def get_all_words(self) -> List[Dict]:
        """获取所有单词"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM words ORDER BY id
            ''')
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def get_word_by_id(self, word_id: int) -> Optional[Dict]:
        """根据ID获取单词"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM words WHERE id = ?', (word_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def update_word(self, word_id: int, **kwargs) -> None:
        """更新单词信息"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            # 构建更新语句
            updates = []
            values = []
            for key, value in kwargs.items():
                updates.append(f"{key} = ?")
                values.append(value)
            
            if updates:
                # 添加 updated_at
                updates.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                
                # WHERE id = ? 必须在最后，word_id 也必须在最后
                sql = f"UPDATE words SET {', '.join(updates)} WHERE id = ?"
                values.append(word_id)  # word_id 放在最后
                
                cursor.execute(sql, values)
                conn.commit()
    
    def delete_word(self, word_id: int) -> None:
        """删除单词"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            # 先删除相关的学习记录
            cursor.execute('DELETE FROM review_history WHERE word_id = ?', (word_id,))
            # 再删除单词
            cursor.execute('DELETE FROM words WHERE id = ?', (word_id,))
            conn.commit()
            logger.info(f"已删除单词 ID: {word_id}")
    
    def get_current_index(self) -> int:
        """获取当前索引"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_state WHERE key = 'current_index'")
            row = cursor.fetchone()
            return int(row['value']) if row else 0
    
    def set_current_index(self, index: int) -> None:
        """设置当前索引"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO app_state (key, value) 
                VALUES ('current_index', ?)
            ''', (str(index),))
            conn.commit()
    
    def add_review_record(self, word_id: int, rating: int) -> None:
        """添加学习记录"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO review_history (word_id, rating, review_time)
                VALUES (?, ?, ?)
            ''', (word_id, rating, datetime.now().isoformat()))
            conn.commit()
    
    def get_review_history(self, limit: int = 20) -> List[Dict]:
        """获取最近的学习记录"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT rh.*, w.word, w.meaning
                FROM review_history rh
                JOIN words w ON rh.word_id = w.id
                ORDER BY rh.review_time DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def get_statistics(self) -> Dict:
        """快速获取统计信息（使用数据库查询，不加载全部数据）"""
        with self._db_connection() as conn:
            cursor = conn.cursor()
            # 使用日期字符串比较（ISO格式：YYYY-MM-DD）
            today = datetime.now().date().isoformat()
            
            # 总单词数
            cursor.execute('SELECT COUNT(*) FROM words')
            total = cursor.fetchone()[0]
            
            # 新单词数（review_count = 0）
            cursor.execute('SELECT COUNT(*) FROM words WHERE review_count = 0')
            new_count = cursor.fetchone()[0]
            
            # 待复习数量（next_review <= today 或 next_review IS NULL）
            cursor.execute('''
                SELECT COUNT(*) FROM words 
                WHERE next_review IS NULL OR next_review <= ?
            ''', (today,))
            review_count = cursor.fetchone()[0]
            
            # 已掌握数量（mastered = 1）
            cursor.execute('SELECT COUNT(*) FROM words WHERE mastered = 1')
            mastered_count = cursor.fetchone()[0]
            
            # 总掌握数（mastered=1 或 next_review > today）
            cursor.execute('''
                SELECT COUNT(*) FROM words 
                WHERE mastered = 1 OR (next_review IS NOT NULL AND next_review > ?)
            ''', (today,))
            total_mastered = cursor.fetchone()[0]
            
            return {
                'total': total,
                'new_count': new_count,
                'review_count': review_count,
                'mastered_count': mastered_count,
                'total_mastered': total_mastered
            }
    
    def migrate_from_json(self, json_data: Dict) -> None:
        """从 JSON 数据迁移到数据库"""
        if not json_data or 'words' not in json_data:
            return
        
        words = json_data.get('words', [])
        if not words:
            return
        
        with self._db_connection() as conn:
            cursor = conn.cursor()
            for word_data in words:
                # 处理日期格式
                next_review = word_data.get('next_review')
                if isinstance(next_review, str):
                    try:
                        datetime.fromisoformat(next_review)
                    except ValueError:
                        next_review = datetime.now().isoformat()
                elif isinstance(next_review, datetime):
                    next_review = next_review.isoformat()
                else:
                    next_review = datetime.now().isoformat()
                
                last_review = word_data.get('last_review')
                if isinstance(last_review, str):
                    try:
                        datetime.fromisoformat(last_review)
                    except ValueError:
                        last_review = None
                elif isinstance(last_review, datetime):
                    last_review = last_review.isoformat()
                else:
                    last_review = None
                
                cursor.execute('''
                    INSERT OR REPLACE INTO words 
                    (word, meaning, review_count, ease_factor, interval_days, 
                     next_review, mastered, last_review, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    word_data.get('word', ''),
                    word_data.get('meaning', ''),
                    word_data.get('review_count', 0),
                    word_data.get('ease_factor', 2.5),
                    word_data.get('interval', 1),
                    next_review,
                    1 if word_data.get('mastered', False) else 0,
                    last_review,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            # 迁移当前索引
            current_index = json_data.get('current_index', 0)
            cursor.execute('''
                INSERT OR REPLACE INTO app_state (key, value) 
                VALUES ('current_index', ?)
            ''', (str(current_index),))
            
            conn.commit()
            logger.info(f"成功迁移 {len(words)} 个单词到数据库")
    
    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict]:
        """将数据库行转换为字典"""
        if row is None:
            return None
        
        result: Dict = {}
        for key in row.keys():
            value = row[key]
            # 转换 mastered 和 review_count
            if key == 'mastered':
                result['mastered'] = bool(value)
            elif key == 'interval_days':
                result['interval'] = value
            elif key == 'id':
                result['id'] = value
            else:
                result[key] = value
        
        # 确保字段名与原有格式一致
        if 'interval_days' in result:
            result['interval'] = result.pop('interval_days')
        
        return result
