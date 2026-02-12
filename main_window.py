"""
主窗口 - 单词卡片应用界面
"""
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QListWidget, QListWidgetItem, QMessageBox,
    QFileDialog, QSplitter, QGroupBox, QProgressBar,
    QDialog, QLineEdit, QDialogButtonBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from word_card import WordCard
from word_manager import WordManager
from db_manager import DatabaseManager
from data_manager import DataManager
from datetime import datetime, timedelta


class AddWordDialog(QDialog):
    """添加单词对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加单词')
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 单词输入
        word_label = QLabel('单词:')
        word_label.setFont(QFont('Arial', 11))
        layout.addWidget(word_label)
        
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText('请输入单词')
        self.word_input.setFont(QFont('Arial', 12))
        self.word_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4ecdc4;
            }
        """)
        layout.addWidget(self.word_input)
        
        # 释义输入
        meaning_label = QLabel('释义:')
        meaning_label.setFont(QFont('Arial', 11))
        layout.addWidget(meaning_label)
        
        self.meaning_input = QLineEdit()
        self.meaning_input.setPlaceholderText('请输入释义')
        self.meaning_input.setFont(QFont('Arial', 12))
        self.meaning_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4ecdc4;
            }
        """)
        layout.addWidget(self.meaning_input)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 设置焦点到单词输入框
        self.word_input.setFocus()
        
        # 回车键确认
        self.word_input.returnPressed.connect(self.meaning_input.setFocus)
        self.meaning_input.returnPressed.connect(self.accept)
        
    def get_word_and_meaning(self):
        """获取输入的单词和释义"""
        word = self.word_input.text().strip()
        meaning = self.meaning_input.text().strip()
        return word, meaning


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.word_manager = WordManager(self.db_manager)
        self.data_manager = DataManager()  # 保留用于迁移
        self.init_ui()
        
        # 延迟加载数据，先显示界面
        QTimer.singleShot(100, self.load_data_async)
        
    def init_ui(self):
        self.setWindowTitle('单词卡片 - 英语学习助手')
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧：单词列表和操作
        left_panel = self.create_left_panel()
        
        # 中间：单词卡片
        card_panel = self.create_card_panel()
        
        # 右侧：统计信息
        stats_panel = self.create_stats_panel()
        
        # 使用分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(card_panel)
        splitter.addWidget(stats_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
    def create_left_panel(self):
        """创建左侧面板：单词列表和管理"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel('单词库')
        title.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(title)
        
        # 单词列表（启用虚拟模式以提高性能）
        self.word_list = QListWidget()
        self.word_list.itemClicked.connect(self.on_word_selected)
        # 设置最大显示项数，避免一次性渲染太多项
        layout.addWidget(self.word_list)
        
        # 操作按钮组
        btn_group = QGroupBox('操作')
        btn_layout = QVBoxLayout()
        
        # 添加单词
        btn_add = QPushButton('➕ 添加单词')
        btn_add.clicked.connect(self.add_word)
        btn_layout.addWidget(btn_add)
        
        # 导入单词
        btn_import = QPushButton('📥 导入单词')
        btn_import.clicked.connect(self.import_words)
        btn_layout.addWidget(btn_import)
        
        # 删除单词
        btn_delete = QPushButton('🗑️ 删除单词')
        btn_delete.clicked.connect(self.delete_word)
        btn_layout.addWidget(btn_delete)
        
        # 清空单词库
        btn_clear = QPushButton('🗑️ 清空单词库')
        btn_clear.clicked.connect(self.clear_all_words)
        btn_layout.addWidget(btn_clear)
        
        btn_group.setLayout(btn_layout)
        layout.addWidget(btn_group)
        
        return panel
        
    def create_card_panel(self):
        """创建中间面板：单词卡片"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel('单词卡片')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 单词卡片
        self.word_card = WordCard()
        self.word_card.card_flipped.connect(self.on_card_flipped)
        layout.addWidget(self.word_card, stretch=1)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        # 上一个
        btn_prev = QPushButton('◀ 上一个')
        btn_prev.clicked.connect(self.prev_word)
        btn_layout.addWidget(btn_prev)
        
        # 翻卡
        btn_flip = QPushButton('🔄 翻转')
        btn_flip.clicked.connect(self.flip_card)
        btn_layout.addWidget(btn_flip)
        
        # 下一个
        btn_next = QPushButton('下一个 ▶')
        btn_next.clicked.connect(self.next_word)
        btn_layout.addWidget(btn_next)
        
        layout.addLayout(btn_layout)
        
        # 记忆反馈按钮
        feedback_layout = QHBoxLayout()
        
        btn_forgot = QPushButton('❌ 忘记')
        btn_forgot.setStyleSheet("background-color: #ff6b6b; color: white; font-weight: bold; font-size: 14px; padding: 10px;")
        btn_forgot.clicked.connect(self.rate_word_forgot)
        feedback_layout.addWidget(btn_forgot)
        
        btn_mastered = QPushButton('✅ 掌握')
        btn_mastered.setStyleSheet("background-color: #4ecdc4; color: white; font-weight: bold; font-size: 14px; padding: 10px;")
        btn_mastered.clicked.connect(self.rate_word_mastered)
        btn_mastered.setEnabled(True)  # 确保按钮启用
        feedback_layout.addWidget(btn_mastered)
        
        layout.addLayout(feedback_layout)
        
        return panel
        
    def create_stats_panel(self):
        """创建右侧面板：统计信息"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel('学习统计')
        title.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(title)
        
        # 总览信息组（新增）
        overview_group = QGroupBox('总览')
        overview_layout = QVBoxLayout()
        
        self.label_total_words = QLabel('总单词数: 0')
        self.label_total_words.setFont(QFont('Arial', 12, QFont.Bold))
        overview_layout.addWidget(self.label_total_words)
        
        self.label_total_mastered = QLabel('总掌握数: 0')
        self.label_total_mastered.setFont(QFont('Arial', 12, QFont.Bold))
        overview_layout.addWidget(self.label_total_mastered)
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # 统计信息组
        stats_group = QGroupBox('今日学习')
        stats_layout = QVBoxLayout()
        
        self.label_total = QLabel('总单词数: 0')
        stats_layout.addWidget(self.label_total)
        
        self.label_new = QLabel('新单词: 0')
        stats_layout.addWidget(self.label_new)
        
        self.label_review = QLabel('待复习: 0')
        stats_layout.addWidget(self.label_review)
        
        self.label_mastered = QLabel('已掌握: 0')
        stats_layout.addWidget(self.label_mastered)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        stats_layout.addWidget(self.progress_bar)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 学习记录组
        record_group = QGroupBox('最近学习')
        record_layout = QVBoxLayout()
        
        self.record_text = QTextEdit()
        self.record_text.setReadOnly(True)
        self.record_text.setMaximumHeight(200)
        record_layout.addWidget(self.record_text)
        
        record_group.setLayout(record_layout)
        layout.addWidget(record_group)
        
        layout.addStretch()
        
        return panel
        
    def load_data_async(self):
        """异步加载数据（优化启动速度）"""
        self.statusBar().showMessage('正在加载数据...')
        QApplication.processEvents()  # 刷新界面
        
        # 快速检查数据库是否有数据（只检查数量，不加载全部）
        word_count = self.db_manager.get_word_count()
        
        # 如果数据库为空，尝试从 JSON 文件迁移
        if word_count == 0:
            json_data = self.data_manager.load()
            if json_data and json_data.get('words'):
                # 询问用户是否迁移
                reply = QMessageBox.question(
                    self, '数据迁移',
                    f'检测到 JSON 文件中有 {len(json_data.get("words", []))} 个单词，\n'
                    '是否要迁移到数据库？',
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.db_manager.migrate_from_json(json_data)
                    self.word_manager._invalidate_cache()  # 清除缓存
                    QMessageBox.information(self, '迁移成功', '数据已成功迁移到数据库！')
        
        # 从数据库加载当前索引
        self.word_manager.current_index = self.db_manager.get_current_index()
        
        # 延迟加载学习记录（非关键数据）
        QTimer.singleShot(200, self.load_review_history)
        
        # 更新显示
        self.update_display()
        self.statusBar().showMessage('就绪')
    
    def load_data(self):
        """加载数据（保留用于兼容性）"""
        self.load_data_async()
        
    def save_data(self):
        """保存数据 - 数据库会自动保存，这里只需要保存当前索引"""
        # 当前索引已经在设置时自动保存到数据库
        # 这个方法保留用于兼容性
        pass
    
    def load_review_history(self):
        """加载学习记录到界面"""
        history = self.db_manager.get_review_history(limit=50)
        self.record_text.clear()
        rating_map = {1: '忘记', 2: '掌握'}
        for record in reversed(history):  # 反转以显示最新的在前面
            word = record.get('word', '')
            rating = record.get('rating', 0)
            review_time = record.get('review_time', '')
            rating_text = rating_map.get(rating, '未知')
            
            # 格式化时间
            try:
                if isinstance(review_time, str):
                    dt = datetime.fromisoformat(review_time)
                    time_str = dt.strftime('%H:%M')
                else:
                    time_str = str(review_time)
            except:
                time_str = review_time
            
            record_line = f"{time_str} - {word}: {rating_text}\n"
            self.record_text.append(record_line)
        
    def update_display(self):
        """更新显示"""
        # 获取单词列表（使用缓存，避免重复查询）
        words = self.word_manager.words
        
        # 如果单词数量很大，使用批量更新优化性能
        word_count = len(words)
        if word_count > 1000:
            # 大量单词时，先暂停更新以提高性能
            self.word_list.setUpdatesEnabled(False)
        
        # 更新单词列表
        self.word_list.clear()
        now = datetime.now()
        
        for i, word_data in enumerate(words):
            word = word_data['word']
            next_review = word_data.get('next_review')
            
            # 解析日期
            next_review_dt = None
            if next_review:
                if isinstance(next_review, str):
                    try:
                        next_review_dt = datetime.fromisoformat(next_review)
                    except (ValueError, AttributeError):
                        # 如果解析失败，视为需要复习
                        next_review_dt = datetime.now() - timedelta(days=1)
                elif isinstance(next_review, datetime):
                    next_review_dt = next_review
                else:
                    next_review_dt = datetime.now() - timedelta(days=1)
            else:
                # 如果没有设置下次复习时间，视为需要复习
                next_review_dt = datetime.now() - timedelta(days=1)
            
            # 显示待复习标记
            # 只比较日期部分（忽略时间）
            next_review_date = next_review_dt.date()
            today = now.date()
            
            if word_data.get('mastered', False):
                # 已掌握的单词显示绿色
                item_text = f"✅ {word}"
            elif next_review_date <= today:
                # 需要复习的单词显示红色（今天或过去的日期）
                item_text = f"🔴 {word}"
            else:
                # 未来的日期，显示绿色（已掌握，待复习但时间未到）
                item_text = f"✅ {word}"
                
            item = QListWidgetItem(item_text)
            if i == self.word_manager.current_index:
                item.setBackground(QColor(200, 220, 255))
            self.word_list.addItem(item)
        
        # 恢复更新（如果之前暂停了）
        if word_count > 1000:
            self.word_list.setUpdatesEnabled(True)
        
        # 更新统计（使用数据库查询，避免遍历大量数据）
        stats = self.db_manager.get_statistics()
        
        total = stats['total']
        new_count = stats['new_count']
        review_count = stats['review_count']
        mastered_count = stats['mastered_count']
        total_mastered = stats['total_mastered']
        
        # 更新总览信息
        self.label_total_words.setText(f'总单词数: {total}')
        self.label_total_mastered.setText(f'总掌握数: {total_mastered}')
        
        # 更新今日学习信息
        self.label_total.setText(f'总单词数: {total}')
        self.label_new.setText(f'新单词: {new_count}')
        self.label_review.setText(f'待复习: {review_count}')
        self.label_mastered.setText(f'已掌握: {mastered_count}')
        
        if total > 0:
            progress = int((mastered_count / total) * 100)
            self.progress_bar.setValue(progress)
        
        # 显示当前单词卡片
        if words:
            self.show_current_card()
        else:
            self.word_card.set_word("", "请添加单词开始学习")
            
    def show_current_card(self):
        """显示当前单词卡片"""
        if not self.word_manager.words:
            return
            
        word_data = self.word_manager.get_current_word()
        if not word_data:
            return
            
        self.word_card.set_word(word_data['word'], word_data['meaning'])
        self.word_card.reset_flip()
        
        # 高亮当前单词
        if self.word_manager.current_index < self.word_list.count():
            self.word_list.setCurrentRow(self.word_manager.current_index)
        
    def on_word_selected(self, item):
        """单词列表项被选中"""
        row = self.word_list.row(item)
        self.word_manager.current_index = row
        self.show_current_card()
        
    def flip_card(self):
        """翻转卡片"""
        self.word_card.flip()
        
    def on_card_flipped(self, is_flipped):
        """卡片翻转事件"""
        if is_flipped:
            self.statusBar().showMessage('已显示释义，请评估记忆情况')
        else:
            self.statusBar().showMessage('显示单词')
            
    def prev_word(self):
        """上一个单词"""
        if not self.word_manager.words:
            return
        self.word_manager.prev_word()
        # 确保索引有效
        if self.word_manager.current_index < 0:
            self.word_manager.current_index = len(self.word_manager.words) - 1
        self.show_current_card()
        self.update_display()
        
    def next_word(self):
        """下一个单词"""
        if not self.word_manager.words:
            return
        self.word_manager.next_word()
        # 确保索引有效
        if self.word_manager.current_index >= len(self.word_manager.words):
            self.word_manager.current_index = 0
        self.show_current_card()
        self.update_display()
        
    def rate_word_forgot(self):
        """点击忘记按钮"""
        self.rate_word(1)
    
    def rate_word_mastered(self):
        """点击掌握按钮"""
        self.statusBar().showMessage('正在处理掌握评价...', 1000)
        QApplication.processEvents()
        self.rate_word(2)
    
    def rate_word(self, rating):
        """评价单词记忆情况 (1=忘记, 2=掌握)"""
        try:
            rating_text = ['', '忘记', '掌握'][rating]
            self.statusBar().showMessage(f'正在评价: {rating_text}...')
            
            if not self.word_manager.words:
                self.statusBar().showMessage('单词库为空')
                QMessageBox.warning(self, '提示', '单词库为空，无法评价')
                return
                
            word_data = self.word_manager.get_current_word()
            if not word_data:
                self.statusBar().showMessage('无法获取当前单词')
                QMessageBox.warning(self, '提示', '无法获取当前单词')
                return
            
            # 保存当前单词索引和单词ID
            current_idx = self.word_manager.current_index
            word_id = word_data.get('id')
            word = word_data.get('word', '未知')
            
            if not word_id:
                self.statusBar().showMessage('单词ID无效')
                QMessageBox.warning(self, '错误', f'单词 "{word}" 的ID无效')
                return
                
            # 执行评价（更新数据库）
            self.word_manager.rate_word(rating)
            
            # 强制清除缓存，确保使用最新数据
            self.word_manager._invalidate_cache()
            
            # 恢复当前索引（在重新加载数据之前）
            # 先获取单词数量，避免加载全部数据
            word_count = self.db_manager.get_word_count()
            if current_idx < word_count:
                self.word_manager.current_index = current_idx
            
            # 延迟重新加载学习记录（非关键操作）
            QTimer.singleShot(100, self.load_review_history)
            
            # 立即更新显示（在切换到下一个单词之前）
            self.update_display()
            QApplication.processEvents()
            
            # 自动翻到下一张
            QTimer.singleShot(500, self.next_word)
            
            # 数据库会自动保存，但确保索引已保存
            self.save_data()
            
            rating_text = ['', '忘记', '掌握'][rating]
            self.statusBar().showMessage(f'已记录: {rating_text}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'评价单词时出错: {str(e)}')
        
    def add_word(self):
        """添加单词"""
        dialog = AddWordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            word, meaning = dialog.get_word_and_meaning()
            if not word or not meaning:
                QMessageBox.warning(self, '输入错误', '单词和释义不能为空！')
                return
            
            self.word_manager.add_word(word, meaning)
            self.word_manager._invalidate_cache()  # 清除缓存
            self.save_data()
            self.update_display()
            self.statusBar().showMessage(f'已添加: {word}')
        
    def delete_word(self):
        """删除单词"""
        if not self.word_manager.words:
            QMessageBox.warning(self, '警告', '单词库为空')
            return
            
        reply = QMessageBox.question(
            self, '确认删除', 
            f'确定要删除单词 "{self.word_manager.get_current_word()["word"]}" 吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.word_manager.delete_current_word()
            self.word_manager._invalidate_cache()  # 清除缓存
            self.save_data()
            self.update_display()
            self.statusBar().showMessage('已删除')
    
    def clear_all_words(self):
        """清空单词库"""
        count = self.db_manager.get_word_count()
        if count == 0:
            QMessageBox.information(self, '提示', '单词库已经是空的')
            return
        reply = QMessageBox.question(
            self, '确认清空',
            f'确定要清空整个单词库吗？将删除全部 {count} 个单词及学习记录，此操作不可恢复。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db_manager.clear_all_words()
            self.word_manager._invalidate_cache()
            self.update_display()
            self.word_card.set_word('', '')
            self.record_text.clear()
            self.statusBar().showMessage('已清空单词库')
            
    def import_words(self):
        """导入单词"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '导入单词', '', 
            'Text Files (*.txt);;JSON Files (*.json);;All Files (*)'
        )
        
        if not file_path:
            return
            
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    words = data.get('words', [])
            else:
                # 文本格式：每行 "单词|释义" 或 "单词 释义"
                words = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        if '|' in line:
                            word, meaning = line.split('|', 1)
                        else:
                            parts = line.split(None, 1)
                            if len(parts) >= 2:
                                word, meaning = parts[0], parts[1]
                            else:
                                continue
                        words.append({'word': word.strip(), 'meaning': meaning.strip()})
            
            count = 0
            for word_data in words:
                if 'word' in word_data and 'meaning' in word_data:
                    self.word_manager.add_word(word_data['word'], word_data['meaning'])
                    count += 1
            
            # 清除缓存以刷新显示
            self.word_manager._invalidate_cache()
            self.save_data()
            self.update_display()
            QMessageBox.information(self, '导入成功', f'成功导入 {count} 个单词')
            self.statusBar().showMessage(f'已导入 {count} 个单词')
            
        except Exception as e:
            QMessageBox.critical(self, '导入失败', f'导入时出错: {str(e)}')
            
    def closeEvent(self, event):
        """关闭事件"""
        self.save_data()
        event.accept()
