#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动器 - 显示启动画面，延迟加载重模块
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QVBoxLayout,
    QWidget,
)
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
        
        # 设置窗口图标
        try:
            from PyQt6.QtGui import QIcon
            if os.path.exists("whg3r-qi1nv-001.ico"):
                self.setWindowIcon(QIcon("whg3r-qi1nv-001.ico"))
        except:
            pass
        
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
        title_label = QLabel("安全登录")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            color: #2c3e50;
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        """)
        main_layout.addWidget(title_label)
        
        # 版本信息
        from version import get_version
        version_label = QLabel(f"v{get_version()}")
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
    # 如果不需要启动画面，直接运行主程序
    NO_SPLASH = os.environ.get('NO_SPLASH', 'false').lower() == 'true'
    
    if NO_SPLASH:
        # 直接运行主程序，无启动画面
        from desktop_app import DHIDesktopApp
        app = DHIDesktopApp()
        sys.exit(app.run())
    
    # 1. 创建应用程序和启动画面（很快）
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    try:
        from PyQt6.QtGui import QIcon
        if os.path.exists("whg3r-qi1nv-001.ico"):
            app.setWindowIcon(QIcon("whg3r-qi1nv-001.ico"))
    except:
        pass
    
    splash = SplashWindow()
    splash.show()
    QApplication.processEvents()
    
    # 保存窗口和线程引用，避免 Qt 对象提前回收。
    main_window = None
    update_check_worker = None
    update_download_worker = None
    update_progress = None
    
    # 2. 延迟导入并启动主程序
    def load_and_start():
        nonlocal main_window
        try:
            splash.update_loading_text("加载核心模块...")
            
            # 导入主程序需要的模块
            from desktop_app import SimpleAuthService, LoginDialog, MainWindow
            from PyQt6.QtWidgets import QDialog, QMessageBox
            from PyQt6.QtGui import QIcon
            
            splash.update_loading_text("初始化程序...")
            
            # 设置应用程序信息（从DHIDesktopApp.run()复制）
            app.setApplicationName("DHI筛查助手")
            from version import get_version
            app.setApplicationVersion(get_version())
            app.setOrganizationName("DHI")
            app.setOrganizationDomain("dhi.com")
            app.setStyle('Fusion')
            
            # 设置应用程序图标
            try:
                if os.path.exists("whg3r-qi1nv-001.ico"):
                    app.setWindowIcon(QIcon("whg3r-qi1nv-001.ico"))
            except:
                pass
            
            splash.update_loading_text("连接认证服务...")
            
            # 创建认证服务
            auth_service = SimpleAuthService()
            
            # 检查认证服务
            if not auth_service.check_server_health():
                splash.close()
                QMessageBox.critical(
                    None,
                    "认证服务不可用",
                    "暂时无法连接认证服务。\n请检查网络连接后重试。"
                )
                app.quit()
                return
            
            # 更新启动画面文本
            splash.update_loading_text("请登录...")
            
            # 强制启动画面到后台
            splash.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
            splash.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
            splash.show()  # 重新显示以应用新的窗口标志
            splash.lower()
            
            # 创建登录对话框
            login_dialog = LoginDialog(None, auth_service)
            
            # 设置登录窗口为模态对话框
            login_dialog.setModal(True)
            login_dialog.setWindowFlags(
                Qt.WindowType.Dialog | 
                Qt.WindowType.WindowCloseButtonHint |
                Qt.WindowType.WindowTitleHint
            )
            
            # 显示并激活登录窗口
            login_dialog.show()
            login_dialog.raise_()
            login_dialog.activateWindow()
            
            # 只在初始显示后短暂确保窗口在前面（避免干扰注册等子窗口）
            QTimer.singleShot(200, lambda: login_dialog.raise_())
            
            if login_dialog.exec() == QDialog.DialogCode.Accepted:
                username = login_dialog.get_username()
                
                # 登录成功，关闭启动画面
                splash.close()
                
                # 创建主窗口
                main_window = MainWindow(username=username, auth_service=auth_service)
                main_window.showMaximized()
                
                # 主窗口创建成功，继续运行事件循环
            else:
                # 用户取消登录
                splash.close()
                app.quit()
            
        except Exception as e:
            splash.close()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "启动错误", f"程序启动失败：\n{str(e)}")
            app.quit()

    def start_application_after_update_check():
        splash.show()
        splash.update_loading_text("加载核心模块...")
        QTimer.singleShot(100, load_and_start)

    def handle_update_downloaded(installer_path):
        nonlocal update_progress
        from pathlib import Path
        from update_manager import launch_installer

        if update_progress:
            update_progress.close()
        try:
            launch_installer(Path(installer_path))
            app.quit()
        except Exception:
            QMessageBox.critical(None, "更新失败", "无法启动安装程序，请稍后重试")
            start_application_after_update_check()

    def handle_update_download_failed(message):
        nonlocal update_progress
        if update_progress:
            update_progress.close()
        QMessageBox.warning(None, "更新失败", message)
        start_application_after_update_check()

    def download_update(manifest):
        nonlocal update_download_worker, update_progress
        from update_workers import UpdateDownloadWorker

        update_progress = QProgressDialog("正在下载并校验更新包...", None, 0, 100)
        update_progress.setWindowTitle("软件更新")
        update_progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        update_progress.setCancelButton(None)
        update_progress.setAutoClose(False)
        update_progress.show()

        update_download_worker = UpdateDownloadWorker(manifest)
        update_download_worker.progress.connect(update_progress.setValue)
        update_download_worker.completed.connect(handle_update_downloaded)
        update_download_worker.failed.connect(handle_update_download_failed)
        update_download_worker.start()

    def handle_update_result(manifest):
        if not manifest:
            start_application_after_update_check()
            return

        splash.close()
        changes = "\n".join(f"• {item}" for item in manifest.get("changes", []))
        prompt = (
            f"发现新版本 v{manifest['version']}。\n\n"
            f"{changes or '包含功能改进和安全更新。'}\n\n"
            "是否现在下载并安装？"
        )
        if manifest.get("force_update"):
            QMessageBox.information(None, "需要更新", prompt.replace("是否现在", "即将"))
            download_update(manifest)
            return

        choice = QMessageBox.question(
            None,
            "发现新版本",
            prompt,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if choice == QMessageBox.StandardButton.Yes:
            download_update(manifest)
        else:
            start_application_after_update_check()

    def begin_update_check():
        nonlocal update_check_worker
        from update_workers import UpdateCheckWorker

        splash.update_loading_text("检查软件更新...")
        update_check_worker = UpdateCheckWorker()
        update_check_worker.completed.connect(handle_update_result)
        update_check_worker.failed.connect(lambda _message: start_application_after_update_check())
        update_check_worker.start()
    
    # 3. 使用定时器延迟加载（让启动画面先显示）
    QTimer.singleShot(300, begin_update_check)
    
    # 4. 运行事件循环
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
