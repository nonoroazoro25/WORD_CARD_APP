"""
主窗口 - 单词卡片应用界面
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QFileDialog, QSplitter, QGroupBox,
    QDialog, QLineEdit, QDialogButtonBox, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
from word_card import WordCard
from word_manager import WordManager
from db_manager import DatabaseManager
from data_manager import DataManager
from datetime import datetime, timedelta


# 饼图已掌握颜色（与图例一致）
PIE_MASTERED_COLOR = QColor(78, 205, 196)

# 布局常量（统一边距与间距）
LAYOUT_MARGIN = 16
LAYOUT_SPACING = 12
PANEL_TITLE_FONT_SIZE = 14
CARD_TITLE_FONT_SIZE = 16
LEFT_PANEL_MIN_WIDTH = 220
CARD_PANEL_MIN_WIDTH = 420
STATS_PANEL_MIN_WIDTH = 200


class PieChartWidget(QWidget):
    """饼状图：显示新单词、待复习、已掌握比例，中心为已掌握占总数的比例"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._total = 0
        self._new_count = 0
        self._review_count = 0
        self._mastered_count = 0
    
    def set_data(self, total, new_count, review_count, mastered_count):
        self._total = total
        self._new_count = new_count
        self._review_count = review_count
        self._mastered_count = mastered_count
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        w, h = self.width(), self.height()
        side = min(w, h) - 10
        x0 = (w - side) / 2
        y0 = (h - side) / 2
        rect = QRectF(x0, y0, side, side)
        
        if self._total <= 0:
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.setPen(QPen(QColor(160, 160, 160), 1))
            painter.drawPie(rect, 0, 360 * 16)
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(rect, Qt.AlignCenter, '暂无数据')
            return
        
        # 饼图按总单词数比例画，使中心“已掌握%”= 已掌握/总数 与扇形一致
        total = max(self._total, 1)
        # 已掌握扇形（占比 = 已掌握/总数）
        mastered_span = int((self._mastered_count / total) * 360 * 16)
        # 剩余角度分给 新单词 和 待复习（按二者在“未掌握”中的比例）
        rest = self._total - self._mastered_count
        rest_angle = 360 * 16 - mastered_span
        if rest <= 0:
            new_span = 0
            review_span = 0
        else:
            new_span = int((self._new_count / rest) * rest_angle)
            review_span = rest_angle - new_span
        start_angle = 90 * 16
        # 绘制顺序：新单词、待复习、已掌握（与之前一致）
        for color, span in [
            (QColor(126, 184, 218), new_span),
            (QColor(255, 138, 128), review_span),
            (PIE_MASTERED_COLOR, mastered_span),
        ]:
            if span <= 0:
                continue
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(220, 220, 220), 1))
            painter.drawPie(rect, start_angle, span)
            start_angle += span
        
        # 中心：已掌握比例 = 已掌握数 / 总单词数（与扇形一致）
        cx, cy = rect.center().x(), rect.center().y()
        inner_r = side * 0.42
        inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
        painter.setBrush(QBrush(QColor(0xe2, 0xe0, 0xda)))
        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.drawEllipse(inner_rect)
        mastered_pct = round((self._mastered_count / total) * 100)
        mastered_pct = min(100, max(0, mastered_pct))
        painter.setPen(QColor(45, 45, 45))
        font = QFont('Arial', 13, QFont.Bold)
        painter.setFont(font)
        painter.drawText(inner_rect, Qt.AlignCenter, f'{mastered_pct}%\n已掌握')


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
                font-size: 14px;
                color: #2d2d2d;
                background-color: #e2e0da;
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
                border: 2px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
                color: #2d2d2d;
                background-color: #e2e0da;
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


class EditWordDialog(QDialog):
    """编辑单词对话框"""
    def __init__(self, word, meaning, parent=None):
        super().__init__(parent)
        self.setWindowTitle('编辑单词')
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui(word, meaning)
        
    def init_ui(self, word, meaning):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 单词输入
        word_label = QLabel('单词:')
        word_label.setFont(QFont('Arial', 11))
        layout.addWidget(word_label)
        
        self.word_input = QLineEdit()
        self.word_input.setText(word)
        self.word_input.setFont(QFont('Arial', 12))
        self.word_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                color: #2d2d2d;
                background-color: #e2e0da;
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
        self.meaning_input.setText(meaning)
        self.meaning_input.setFont(QFont('Arial', 12))
        self.meaning_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
                color: #2d2d2d;
                background-color: #e2e0da;
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
        
        # 设置焦点到单词输入框并选中所有文本
        self.word_input.setFocus()
        self.word_input.selectAll()
        
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
        
        # 主布局（统一边距，避免贴边）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(LAYOUT_MARGIN, LAYOUT_MARGIN, LAYOUT_MARGIN, LAYOUT_MARGIN)
        main_layout.setSpacing(0)
        
        # 左侧：单词列表和操作
        left_panel = self.create_left_panel()
        
        # 中间：单词卡片
        card_panel = self.create_card_panel()
        
        # 右侧：统计信息
        stats_panel = self.create_stats_panel()
        
        # 分割器：设置最小宽度，保证三栏比例协调
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(card_panel)
        splitter.addWidget(stats_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        left_panel.setMinimumWidth(LEFT_PANEL_MIN_WIDTH)
        card_panel.setMinimumWidth(CARD_PANEL_MIN_WIDTH)
        stats_panel.setMinimumWidth(STATS_PANEL_MIN_WIDTH)
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
    def create_left_panel(self):
        """创建左侧面板：单词列表和管理"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(LAYOUT_MARGIN // 2, 0, LAYOUT_MARGIN // 2, 0)
        layout.setSpacing(LAYOUT_SPACING)
        
        # 标题（与右侧统计标题字号一致）
        title = QLabel('单词库')
        title.setFont(QFont('Arial', PANEL_TITLE_FONT_SIZE, QFont.Bold))
        layout.addWidget(title)
        
        # 单词列表
        self.word_list = QListWidget()
        self.word_list.setMinimumHeight(200)
        self.word_list.itemClicked.connect(self.on_word_selected)
        self.word_list.itemDoubleClicked.connect(self.on_word_double_clicked)
        layout.addWidget(self.word_list)
        
        # 操作按钮组（统一间距）
        btn_group = QGroupBox('操作')
        btn_group.setContentsMargins(LAYOUT_MARGIN // 2, LAYOUT_MARGIN, LAYOUT_MARGIN // 2, LAYOUT_MARGIN // 2)
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        
        btn_add = QPushButton('➕ 添加单词')
        btn_add.clicked.connect(self.add_word)
        btn_layout.addWidget(btn_add)
        
        btn_import = QPushButton('📥 导入单词')
        btn_import.clicked.connect(self.import_words)
        btn_layout.addWidget(btn_import)
        
        btn_delete = QPushButton('🗑️ 删除单词')
        btn_delete.clicked.connect(self.delete_word)
        btn_layout.addWidget(btn_delete)
        
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
        layout.setContentsMargins(LAYOUT_MARGIN, 0, LAYOUT_MARGIN, 0)
        layout.setSpacing(LAYOUT_SPACING)
        
        # 标题
        title = QLabel('单词卡片')
        title.setFont(QFont('Arial', CARD_TITLE_FONT_SIZE, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 单词卡片
        self.word_card = WordCard()
        self.word_card.card_flipped.connect(self.on_card_flipped)
        layout.addWidget(self.word_card, stretch=1)
        
        # 上一个/下一个（居中、等宽、等距）
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        
        btn_prev = QPushButton('◀ 上一个')
        btn_prev.setMinimumWidth(110)
        btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #c0c4c0;
                color: #2d2d2d;
                border: 1px solid #a8aca8;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4b8b4;
                border-color: #4ecdc4;
                color: #1a1a1a;
            }
            QPushButton:pressed { background-color: #a8aca8; color: #1a1a1a; }
            QPushButton:disabled { color: #7a7a7a; background-color: #c8ccc8; }
        """)
        btn_prev.clicked.connect(self.prev_word)
        btn_layout.addWidget(btn_prev)
        btn_layout.addSpacing(LAYOUT_MARGIN)
        
        btn_next = QPushButton('下一个 ▶')
        btn_next.setMinimumWidth(110)
        btn_next.setStyleSheet("""
            QPushButton {
                background-color: #c0c4c0;
                color: #2d2d2d;
                border: 1px solid #a8aca8;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4b8b4;
                border-color: #4ecdc4;
                color: #1a1a1a;
            }
            QPushButton:pressed { background-color: #a8aca8; color: #1a1a1a; }
            QPushButton:disabled { color: #7a7a7a; background-color: #c8ccc8; }
        """)
        btn_next.clicked.connect(self.next_word)
        btn_layout.addWidget(btn_next)
        
        btn_layout.addStretch(1)
        layout.addLayout(btn_layout)
        
        self.btn_prev = btn_prev
        self.btn_next = btn_next
        
        # 记忆反馈按钮（居中、等宽、等距）
        feedback_layout = QHBoxLayout()
        feedback_layout.addStretch(1)
        
        btn_forgot = QPushButton('❌ 忘记')
        btn_forgot.setMinimumWidth(180)
        btn_forgot.setMinimumHeight(60)
        btn_forgot.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: #fff;
                font-weight: bold;
                font-size: 18px;
                padding: 16px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #ff5252; }
            QPushButton:pressed { background-color: #e04545; }
        """)
        btn_forgot.clicked.connect(self.rate_word_forgot)
        feedback_layout.addWidget(btn_forgot)
        feedback_layout.addSpacing(LAYOUT_MARGIN)
        
        btn_mastered = QPushButton('✅ 掌握')
        btn_mastered.setMinimumWidth(180)
        btn_mastered.setMinimumHeight(60)
        btn_mastered.setStyleSheet("""
            QPushButton {
                background-color: #4ecdc4;
                color: #fff;
                font-weight: bold;
                font-size: 18px;
                padding: 16px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #45b7aa; }
            QPushButton:pressed { background-color: #3da99e; }
        """)
        btn_mastered.clicked.connect(self.rate_word_mastered)
        btn_mastered.setEnabled(True)
        feedback_layout.addWidget(btn_mastered)
        feedback_layout.addStretch(1)
        
        layout.addLayout(feedback_layout)
        
        return panel
        
    def create_stats_panel(self):
        """创建右侧面板：学习统计图示"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(LAYOUT_MARGIN // 2, 0, LAYOUT_MARGIN // 2, 0)
        layout.setSpacing(LAYOUT_SPACING)
        
        # 标题（与左侧标题字号一致）
        title = QLabel('学习统计')
        title.setFont(QFont('Arial', PANEL_TITLE_FONT_SIZE, QFont.Bold))
        layout.addWidget(title)
        
        # 总单词数
        self.label_total_words = QLabel('共 0 个单词')
        self.label_total_words.setFont(QFont('Arial', 12, QFont.Bold))
        layout.addWidget(self.label_total_words)
        
        # 饼状图（固定比例，避免被拉得过扁）
        self.pie_chart = PieChartWidget(self)
        self.pie_chart.setMinimumSize(180, 180)
        layout.addWidget(self.pie_chart)
        
        # 图例（与饼图对齐）
        self.legend_mastered = QLabel('■ 已掌握 0')
        self.legend_mastered.setStyleSheet(
            "color: #2d7a73; font-size: 12px; font-weight: bold;"
        )
        self.legend_mastered.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.legend_mastered)
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
        
        # 更新显示
        self.update_display()
        self.statusBar().showMessage('就绪')
    
    def save_data(self):
        """兼容接口：数据由数据库自动保存，当前索引在切换时已保存"""
        pass
    
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
            
            # 解析日期，如果解析失败或不存在，视为需要复习
            if next_review:
                try:
                    next_review_dt = datetime.fromisoformat(next_review) if isinstance(next_review, str) else next_review
                except (ValueError, TypeError):
                    next_review_dt = datetime.now() - timedelta(days=1)
            else:
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
        
        # 更新统计饼图（用 total_mastered 表示“已掌握或暂不需复习”，评价后比例会立即变化）
        self.label_total_words.setText(f'共 {total} 个单词')
        self.pie_chart.set_data(total, new_count, review_count, total_mastered)
        self.legend_mastered.setText(f'■ 已掌握 {total_mastered}')
        
        # 显示当前单词卡片
        if words:
            self.show_current_card()
        else:
            self.word_card.set_word("", "请添加单词开始学习")
        
        # 更新上一个/下一个按钮状态
        n = len(words)
        idx = self.word_manager.current_index
        if hasattr(self, 'btn_prev') and hasattr(self, 'btn_next'):
            self.btn_prev.setEnabled(n > 1 and idx > 0)
            self.btn_next.setEnabled(n > 1 and idx < n - 1)
            
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
    
    def on_word_double_clicked(self, item):
        """单词列表项双击事件 - 编辑单词"""
        row = self.word_list.row(item)
        self.word_manager.current_index = row
        self.edit_word()
        
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
            
            # 检查单词是否已存在
            if self.db_manager.word_exists(word):
                QMessageBox.information(self, '提示', f'单词 "{word}" 已存在')
                return
            
            word_id = self.word_manager.add_word(word, meaning)
            if word_id:
                self.word_manager._invalidate_cache()  # 清除缓存
                self.save_data()
                self.update_display()
                self.statusBar().showMessage(f'已添加: {word}')
        
    def edit_word(self):
        """编辑单词"""
        if not self.word_manager.words:
            QMessageBox.warning(self, '警告', '单词库为空')
            return
        
        word_data = self.word_manager.get_current_word()
        if not word_data:
            return
        
        dialog = EditWordDialog(word_data['word'], word_data['meaning'], self)
        if dialog.exec_() == QDialog.Accepted:
            new_word, new_meaning = dialog.get_word_and_meaning()
            if not new_word or not new_meaning:
                QMessageBox.warning(self, '输入错误', '单词和释义不能为空！')
                return
            
            # 检查新单词是否与其他单词重复（排除当前单词）
            word_id = word_data.get('id')
            if word_id:
                # 检查是否与其他单词重复
                existing_word = self.db_manager.get_word_by_id(word_id)
                if existing_word and new_word.lower() != existing_word['word'].lower():
                    # 如果单词改变了，检查是否与其他单词重复
                    if self.db_manager.word_exists(new_word):
                        QMessageBox.information(self, '提示', f'单词 "{new_word}" 已存在')
                        return
                
                # 更新单词和释义
                self.db_manager.update_word(word_id, word=new_word, meaning=new_meaning)
                self.word_manager._invalidate_cache()  # 清除缓存
                self.save_data()
                self.update_display()
                self.statusBar().showMessage(f'已更新: {new_word}')
    
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
            skipped = 0
            for word_data in words:
                if 'word' in word_data and 'meaning' in word_data:
                    word = word_data['word'].strip()
                    meaning = word_data['meaning'].strip()
                    if word and meaning:
                        if not self.db_manager.word_exists(word):
                            self.word_manager.add_word(word, meaning)
                            count += 1
                        else:
                            skipped += 1
            
            # 清除缓存以刷新显示
            self.word_manager._invalidate_cache()
            self.save_data()
            self.update_display()
            
            if skipped > 0:
                QMessageBox.information(self, '导入完成', f'成功导入 {count} 个单词\n跳过 {skipped} 个重复单词')
            else:
                QMessageBox.information(self, '导入成功', f'成功导入 {count} 个单词')
            self.statusBar().showMessage(f'已导入 {count} 个单词')
            
        except Exception as e:
            QMessageBox.critical(self, '导入失败', f'导入时出错: {str(e)}')
            
    def closeEvent(self, event):
        """关闭事件"""
        self.save_data()
        event.accept()
