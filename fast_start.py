#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动器 - 显示启动画面，延迟加载重模块
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QFont

class SplashWindow(QWidget):
    """启动画面窗口"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 窗口设置
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建背景
        background = QLabel()
        background.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(background)
        
        # Logo或图标
        icon_label = QLabel("🥛")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        main_layout.addWidget(icon_label)
        
        # 标题
        title_label = QLabel("DHI筛查助手")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            color: #2c3e50;
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        """)
        main_layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("v4.02")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 14px;
        """)
        main_layout.addWidget(version_label)
        
        # 加载提示
        self.loading_label = QLabel("正在启动...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            color: #34495e;
            font-size: 12px;
            margin-top: 20px;
        """)
        main_layout.addWidget(self.loading_label)
        
        # 添加进度条
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                text-align: center;
                height: 6px;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
        """)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)  # 无限循环模式
        main_layout.addWidget(self.progress)
        
        layout.addWidget(background)
        self.setLayout(layout)
        
        # 设置窗口大小和位置
        self.resize(300, 200)
        self.center()
        
    def center(self):
        """居中显示窗口"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def update_loading_text(self, text):
        """更新加载提示文本"""
        self.loading_label.setText(text)
        QApplication.processEvents()


def main():
    """快速启动主函数"""
    # 1. 创建应用程序和启动画面（很快）
    app = QApplication(sys.argv)
    splash = SplashWindow()
    splash.show()
    QApplication.processEvents()
    
    # 2. 延迟导入重模块
    def load_main_app():
        try:
            splash.update_loading_text("加载核心模块...")
            
            # 导入必要的模块
            from auth_module import show_login_dialog
            
            splash.update_loading_text("准备登录...")
            
            # 关闭启动画面，显示登录窗口
            splash.close()
            
            # 显示登录对话框
            username = show_login_dialog()
            if not username:
                return 0  # 用户取消登录
            
            # 登录成功后，导入主程序
            from desktop_app import DHIDesktopApp
            
            # 创建并运行主应用
            main_app = DHIDesktopApp()
            exit_code = main_app.run()
            
            return exit_code
            
        except Exception as e:
            splash.close()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "启动错误", f"程序启动失败：\n{str(e)}")
            return 1
    
    # 3. 使用定时器延迟加载（让启动画面先显示）
    QTimer.singleShot(100, lambda: sys.exit(load_main_app()))
    
    # 4. 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()