#!/usr/bin/env python3
"""调试登录问题"""

import sys
from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QLabel

class SimpleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简单测试")
        
        layout = QVBoxLayout()
        
        label = QLabel("点击按钮测试")
        layout.addWidget(label)
        
        btn1 = QPushButton("测试按钮1")
        btn1.clicked.connect(lambda: print("按钮1被点击"))
        layout.addWidget(btn1)
        
        btn2 = QPushButton("测试按钮2")
        btn2.clicked.connect(self.on_button2_clicked)
        layout.addWidget(btn2)
        
        self.setLayout(layout)
        
    def on_button2_clicked(self):
        print("按钮2被点击")
        # 测试创建子对话框
        try:
            child = QDialog(self)
            child.setWindowTitle("子对话框")
            child.resize(200, 100)
            child.exec()
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = SimpleDialog()
    dialog.show()
    sys.exit(app.exec())