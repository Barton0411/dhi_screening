#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动器 - 显示启动画面，延迟加载重模块
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
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
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 30px;
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
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        """)
        main_layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("v4.02")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            color: #bdc3c7;
            font-size: 14px;
        """)
        main_layout.addWidget(version_label)
        
        # 加载提示
        self.loading_label = QLabel("正在启动...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            color: #ecf0f1;
            font-size: 12px;
            margin-top: 20px;
        """)
        main_layout.addWidget(self.loading_label)
        
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
            
            # 导入主程序（这里会花费时间）
            from desktop_app import DHIDesktopApp
            
            splash.update_loading_text("初始化应用程序...")
            
            # 创建主应用
            main_app = DHIDesktopApp()
            
            splash.update_loading_text("准备就绪...")
            
            # 显示主窗口
            exit_code = main_app.run()
            
            # 关闭启动画面
            splash.close()
            
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