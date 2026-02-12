"""
单词卡片组件 - 可翻转的卡片界面
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class WordCard(QWidget):
    """单词卡片组件"""
    card_flipped = pyqtSignal(bool)  # 卡片翻转信号
    
    # 样式常量
    CARD_BASE_STYLE = """
        QLabel {{
            border: 3px solid #4ecdc4;
            border-radius: 15px;
            padding: 40px;
            min-height: 300px;
            {}
        }}
    """
    
    CARD_WORD_STYLE = CARD_BASE_STYLE.format(
        "background-color: white; font-size: 32px; color: #2c3e50;"
    )
    
    CARD_MEANING_STYLE = CARD_BASE_STYLE.format(
        "background-color: #f0f8ff; font-size: 20px; color: #333;"
    )
    
    def __init__(self):
        super().__init__()
        self.is_flipped = False
        self.word = ""
        self.meaning = ""
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 卡片容器（模拟卡片效果）
        self.card_label = QLabel()
        self.card_label.setAlignment(Qt.AlignCenter)
        self.card_label.setWordWrap(True)
        
        # 设置字体
        font = QFont('Arial', 24, QFont.Bold)
        self.card_label.setFont(font)
        
        layout.addWidget(self.card_label)
        
        # 提示文字
        self.hint_label = QLabel('点击"翻转"按钮查看释义')
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.hint_label)
        
    def set_word(self, word, meaning):
        """设置单词和释义"""
        self.word = word
        self.meaning = meaning
        self.reset_flip()
        
    def reset_flip(self):
        """重置翻转状态"""
        self.is_flipped = False
        self.update_display()
        
    def flip(self):
        """翻转卡片"""
        self.is_flipped = not self.is_flipped
        self.update_display()
        self.card_flipped.emit(self.is_flipped)
        
    def update_display(self):
        """更新显示"""
        if not self.word:
            self.card_label.setText("暂无单词")
            self.hint_label.setText("")
            return
            
        if self.is_flipped:
            # 显示释义
            self.card_label.setText(self.meaning)
            self.card_label.setStyleSheet(self.CARD_MEANING_STYLE)
            self.hint_label.setText('已显示释义')
        else:
            # 显示单词
            self.card_label.setText(self.word)
            self.card_label.setStyleSheet(self.CARD_WORD_STYLE)
            self.hint_label.setText('点击"翻转"按钮查看释义')
