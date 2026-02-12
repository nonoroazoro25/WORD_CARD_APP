#!/usr/bin/env python3
"""
CSV 词汇导入工具 - 从CSV文件导入单词到数据库
"""
import csv
import sys
from pathlib import Path
from db_manager import DatabaseManager


def import_csv_to_database(csv_file_path, db_manager):
    """
    从CSV文件导入单词到数据库
    
    Args:
        csv_file_path: CSV文件路径
        db_manager: DatabaseManager实例
        
    Returns:
        tuple: (成功导入数量, 跳过数量, 错误数量)
    """
    csv_path = Path(csv_file_path)
    
    if not csv_path.exists():
        print(f"错误：文件不存在: {csv_path}")
        return (0, 0, 0)
    
    print(f"正在读取CSV文件: {csv_path}")
    
    # 获取数据库中已有的单词（用于去重）
    existing_words = set()
    all_words = db_manager.get_all_words()
    for word_data in all_words:
        existing_words.add(word_data['word'].lower().strip())
    
    print(f"数据库中已有 {len(existing_words)} 个单词")
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    # 收集要导入的单词（用于批量插入）
    words_to_import = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            # 尝试检测分隔符
            sample = f.read(1024)
            f.seek(0)
            
            # 检测分隔符
            delimiter = ','
            if ';' in sample and sample.count(';') > sample.count(','):
                delimiter = ';'
            elif '\t' in sample:
                delimiter = '\t'
            
            reader = csv.reader(f, delimiter=delimiter)
            
            # 跳过标题行
            header = next(reader, None)
            if header:
                print(f"检测到标题行: {header}")
            
            for row_num, row in enumerate(reader, 2):  # 从第2行开始计数
                if len(row) < 2:
                    continue
                
                word = row[0].strip().strip('"\'')  # 去除引号
                meaning = row[1].strip().strip('"\'')  # 去除引号
                
                # 跳过空行或标题行
                if not word or not meaning:
                    continue
                
                # 跳过标题行（如果第一列是"word"）
                if word.lower() == 'word' and row_num == 2:
                    continue
                
                # 去重：检查单词是否已存在（不区分大小写）
                if word.lower() in existing_words:
                    skipped_count += 1
                    continue
                
                # 添加到待导入列表
                words_to_import.append((word, meaning))
                existing_words.add(word.lower())  # 添加到已存在集合（避免同一批次重复）
                
                # 每1000个单词批量插入一次
                if len(words_to_import) >= 1000:
                    added = db_manager.batch_add_words(words_to_import)
                    imported_count += added
                    skipped_count += (len(words_to_import) - added)
                    words_to_import = []
                    
                    if imported_count % 5000 == 0:
                        print(f"已导入 {imported_count} 个单词，跳过 {skipped_count} 个重复单词...")
            
            # 导入剩余的单词
            if words_to_import:
                added = db_manager.batch_add_words(words_to_import)
                imported_count += added
                skipped_count += (len(words_to_import) - added)
    
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        import traceback
        traceback.print_exc()
        return (imported_count, skipped_count, error_count)
    
    return (imported_count, skipped_count, error_count)


def main():
    """主函数"""
    csv_file = '/Users/ssha/Downloads/EnWords.csv'
    
    print("=" * 50)
    print("CSV 词汇导入工具")
    print("=" * 50)
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    # 导入CSV文件
    imported, skipped, errors = import_csv_to_database(csv_file, db_manager)
    
    print("\n" + "=" * 50)
    print("导入完成！")
    print("=" * 50)
    print(f"✅ 成功导入: {imported} 个单词")
    print(f"⏭️  跳过重复: {skipped} 个单词")
    if errors > 0:
        print(f"❌ 导入失败: {errors} 个单词")
    print("=" * 50)


if __name__ == '__main__':
    main()
