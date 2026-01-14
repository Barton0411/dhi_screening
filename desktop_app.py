#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import threading
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import subprocess
import atexit
import requests
import importlib.util

# 设置logger
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QLabel, QPushButton, QFileDialog, QProgressBar, QTextEdit,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QDateEdit, QTableWidget, QTableWidgetItem, 
    QTabWidget, QMessageBox, QSplitter, QHeaderView, QListWidget,
    QListWidgetItem, QFrame, QScrollArea, QMenuBar, QMenu, 
    QDialog, QDialogButtonBox, QSlider, QGridLayout,
    QColorDialog, QInputDialog, QLineEdit, QStyle, QRadioButton,
    QSizePolicy, QProgressDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, QDate, Qt, QTimer, QSettings, QPropertyAnimation, QEasingCurve, pyqtProperty, QDateTime
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QAction
import yaml

# 导入我们的数据处理模块
from data_processor import DataProcessor
from models import FilterConfig

# 导入认证模块
from auth_module import LoginDialog, show_login_dialog
from auth_module.simple_auth_service import SimpleAuthService

# 导入隐性乳房炎监测模块
from mastitis_monitoring import MastitisMonitoringCalculator

# 导入进度条管理器
from progress_manager import SmoothProgressDialog, AsyncProgressManager

# 导入图表本地化
ChinesePlotWidget = None
try:
    # 尝试直接导入
    from chart_localization import ChinesePlotWidget
    logger.info("成功导入 ChinesePlotWidget")
except ImportError as e:
    logger.warning(f"无法导入 ChinesePlotWidget: {e}")
    # 尝试从当前目录导入
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        chart_path = os.path.join(base_dir, 'chart_localization.py')
        if os.path.exists(chart_path):
            spec = importlib.util.spec_from_file_location("chart_localization", chart_path)
            chart_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(chart_module)
            ChinesePlotWidget = chart_module.ChinesePlotWidget
            logger.info(f"从文件路径导入 ChinesePlotWidget: {chart_path}")
        else:
            logger.warning(f"找不到 chart_localization.py: {chart_path}")
    except Exception as e2:
        logger.error(f"从文件导入 ChinesePlotWidget 失败: {e2}")
except Exception as e:
    logger.error(f"导入 ChinesePlotWidget 时出错: {e}")


class DisplaySettingsDialog(QDialog):
    """显示设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("界面显示设置")
        self.setModal(True)
        self.resize(450, 600)
        
        # 加载当前设置
        self.settings = QSettings("DHI", "ProteinScreening")
        current_scale = self.settings.value("display_scale", 100, type=int)
        current_font_color = self.settings.value("font_color", "#000000", type=str)
        current_bg_color = self.settings.value("background_color", "#ffffff", type=str)
        current_font_family = self.settings.value("font_family", "Microsoft YaHei", type=str)
        current_font_size = self.settings.value("font_size", 12, type=int)
        current_font_bold = self.settings.value("font_bold", False, type=bool)
        current_font_italic = self.settings.value("font_italic", False, type=bool)
        current_font_underline = self.settings.value("font_underline", False, type=bool)
        current_use_system_theme = self.settings.value("use_system_theme", True, type=bool)
        
        self.init_ui(current_scale, current_font_color, current_bg_color, 
                    current_font_family, current_font_size, current_font_bold, 
                    current_font_italic, current_font_underline, current_use_system_theme)
    
    def init_ui(self, current_scale, current_font_color, current_bg_color,
                current_font_family, current_font_size, current_font_bold,
                current_font_italic, current_font_underline, current_use_system_theme):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("界面显示设置")
        title_label.setStyleSheet("font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # 缩放设置分组
        scale_group = QGroupBox("显示缩放")
        scale_group.setStyleSheet("QGroupBox { font-weight: bold; color: #333; }")
        scale_layout = QVBoxLayout(scale_group)
        
        # 缩放滑块
        scale_container = QWidget()
        scale_container_layout = QHBoxLayout(scale_container)
        scale_container_layout.setContentsMargins(0, 0, 0, 0)
        
        scale_container_layout.addWidget(QLabel("50%"))
        
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(50, 200)
        self.scale_slider.setValue(current_scale)
        self.scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.scale_slider.setTickInterval(25)
        self.scale_slider.valueChanged.connect(self.update_scale_label)
        scale_container_layout.addWidget(self.scale_slider)
        
        scale_container_layout.addWidget(QLabel("200%"))
        
        scale_layout.addWidget(scale_container)
        
        # 当前缩放显示
        self.scale_label = QLabel(f"当前缩放: {current_scale}%")
        self.scale_label.setStyleSheet("color: #666; font-size: 14px;")
        self.scale_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scale_layout.addWidget(self.scale_label)
        
        scroll_layout.addWidget(scale_group)
        
        # 字体设置分组
        font_group = QGroupBox("字体设置")
        font_group.setStyleSheet("QGroupBox { font-weight: bold; color: #333; }")
        font_layout = QVBoxLayout(font_group)
        
        # 字体系列设置
        font_family_container = QWidget()
        font_family_layout = QHBoxLayout(font_family_container)
        font_family_layout.setContentsMargins(0, 0, 0, 0)
        
        font_family_label = QLabel("字体类型:")
        font_family_label.setStyleSheet("color: #333; min-width: 80px;")
        font_family_layout.addWidget(font_family_label)
        
        self.font_family_combo = QComboBox()
        # 添加常用中文字体
        fonts = [
            "Microsoft YaHei", "SimHei", "SimSun", "KaiTi", "FangSong",
            "Arial", "Times New Roman", "Calibri", "Consolas", "Verdana"
        ]
        self.font_family_combo.addItems(fonts)
        self.font_family_combo.setCurrentText(current_font_family)
        self.font_family_combo.currentTextChanged.connect(self.update_preview)
        font_family_layout.addWidget(self.font_family_combo)
        
        font_layout.addWidget(font_family_container)
        
        # 字体大小设置
        font_size_container = QWidget()
        font_size_layout = QHBoxLayout(font_size_container)
        font_size_layout.setContentsMargins(0, 0, 0, 0)
        
        font_size_label = QLabel("字体大小:")
        font_size_label.setStyleSheet("color: #333; min-width: 80px;")
        font_size_layout.addWidget(font_size_label)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.font_size_spin.setValue(current_font_size)
        self.font_size_spin.setSuffix(" px")
        self.font_size_spin.valueChanged.connect(self.update_preview)
        font_size_layout.addWidget(self.font_size_spin)
        
        font_size_layout.addStretch()
        
        font_layout.addWidget(font_size_container)
        
        # 字体样式设置
        font_style_container = QWidget()
        font_style_layout = QHBoxLayout(font_style_container)
        font_style_layout.setContentsMargins(0, 0, 0, 0)
        
        font_style_label = QLabel("字体样式:")
        font_style_label.setStyleSheet("color: #333; min-width: 80px;")
        font_style_layout.addWidget(font_style_label)
        
        self.font_bold_cb = QCheckBox("加粗")
        self.font_bold_cb.setChecked(current_font_bold)
        self.font_bold_cb.stateChanged.connect(self.update_preview)
        font_style_layout.addWidget(self.font_bold_cb)
        
        self.font_italic_cb = QCheckBox("斜体")
        self.font_italic_cb.setChecked(current_font_italic)
        self.font_italic_cb.stateChanged.connect(self.update_preview)
        font_style_layout.addWidget(self.font_italic_cb)
        
        self.font_underline_cb = QCheckBox("下划线")
        self.font_underline_cb.setChecked(current_font_underline)
        self.font_underline_cb.stateChanged.connect(self.update_preview)
        font_style_layout.addWidget(self.font_underline_cb)
        
        font_style_layout.addStretch()
        
        font_layout.addWidget(font_style_container)
        
        scroll_layout.addWidget(font_group)
        
        # 颜色设置分组
        color_group = QGroupBox("颜色设置")
        color_group.setStyleSheet("QGroupBox { font-weight: bold; color: #333; }")
        color_layout = QVBoxLayout(color_group)
        
        # 系统主题跟随选项
        self.use_system_theme_cb = QCheckBox("跟随系统主题（深色/浅色模式）")
        self.use_system_theme_cb.setChecked(current_use_system_theme)
        self.use_system_theme_cb.setToolTip("自动适配系统的深色或浅色主题")
        self.use_system_theme_cb.stateChanged.connect(self.on_system_theme_toggled)
        color_layout.addWidget(self.use_system_theme_cb)
        
        # 字体颜色设置
        font_color_container = QWidget()
        font_color_layout = QHBoxLayout(font_color_container)
        font_color_layout.setContentsMargins(0, 0, 0, 0)
        
        font_color_label = QLabel("字体颜色:")
        font_color_label.setStyleSheet("color: #333; min-width: 80px;")
        font_color_layout.addWidget(font_color_label)
        
        self.font_color_btn = QPushButton()
        self.font_color_btn.setFixedSize(80, 30)
        self.font_color_btn.clicked.connect(self.choose_font_color)
        self.current_font_color = current_font_color
        self.update_color_button(self.font_color_btn, self.current_font_color)
        font_color_layout.addWidget(self.font_color_btn)
        
        font_color_layout.addStretch()
        
        # 重置为默认黑色按钮
        reset_font_btn = QPushButton("重置为黑色")
        reset_font_btn.setFixedSize(80, 30)
        reset_font_btn.clicked.connect(lambda: self.reset_color('font'))
        reset_font_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        font_color_layout.addWidget(reset_font_btn)
        
        color_layout.addWidget(font_color_container)
        
        # 背景颜色设置
        bg_color_container = QWidget()
        bg_color_layout = QHBoxLayout(bg_color_container)
        bg_color_layout.setContentsMargins(0, 0, 0, 0)
        
        bg_color_label = QLabel("背景颜色:")
        bg_color_label.setStyleSheet("color: #333; min-width: 80px;")
        bg_color_layout.addWidget(bg_color_label)
        
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(80, 30)
        self.bg_color_btn.clicked.connect(self.choose_bg_color)
        self.current_bg_color = current_bg_color
        self.update_color_button(self.bg_color_btn, self.current_bg_color)
        bg_color_layout.addWidget(self.bg_color_btn)
        
        bg_color_layout.addStretch()
        
        # 重置为默认白色按钮
        reset_bg_btn = QPushButton("重置为白色")
        reset_bg_btn.setFixedSize(80, 30)
        reset_bg_btn.clicked.connect(lambda: self.reset_color('bg'))
        reset_bg_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        bg_color_layout.addWidget(reset_bg_btn)
        
        color_layout.addWidget(bg_color_container)
        
        scroll_layout.addWidget(color_group)
        
        # 预览区域
        preview_group = QGroupBox("预览效果")
        preview_group.setStyleSheet("QGroupBox { font-weight: bold; color: #333; }")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QLabel("这是字体和背景色的预览效果\n支持中文和English混合显示\n数字123456789")
        self.preview_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_text.setMinimumHeight(80)
        self.preview_text.setWordWrap(True)
        self.update_preview()
        preview_layout.addWidget(self.preview_text)
        
        scroll_layout.addWidget(preview_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 恢复默认按钮
        restore_btn = QPushButton("恢复默认")
        restore_btn.clicked.connect(self.restore_defaults)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        button_layout.addWidget(restore_btn)
        
        button_layout.addStretch()
        
        # 取消和确定按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def update_color_button(self, button, color):
        """更新颜色按钮的显示"""
        button.setText(color)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {'white' if self.is_dark_color(color) else 'black'};
                border: 2px solid #333;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
    
    def is_dark_color(self, hex_color):
        """判断颜色是否为深色"""
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            # 转换为RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # 计算亮度
            brightness = (r * 0.299 + g * 0.587 + b * 0.114)
            return brightness < 128
        except:
            return False
    
    def choose_font_color(self):
        """选择字体颜色"""
        color = QColorDialog.getColor(QColor(self.current_font_color), self, "选择字体颜色")
        if color.isValid():
            color_hex = color.name()
            
            # 防呆检查：检测亮度过高的颜色
            try:
                hex_color = color_hex.lstrip('#')
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                brightness = (r * 0.299 + g * 0.587 + b * 0.114) / 255
                
                if brightness > 0.9:
                    reply = QMessageBox.question(
                        self,
                        "字体颜色过浅提醒",
                        f"⚠️ 您选择的颜色 {color_hex} 过于浅淡（亮度{brightness:.1%}）！\n\n"
                        "在白色背景上可能看不清文字。\n\n"
                        "建议选择深色字体以确保良好的可读性。\n\n"
                        "是否仍要使用这个颜色？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        return  # 取消设置，保持原颜色
            except:
                pass  # 如果检查失败，继续使用用户选择的颜色
            
            self.current_font_color = color_hex
            self.update_color_button(self.font_color_btn, self.current_font_color)
            self.update_preview()
    
    def choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor(QColor(self.current_bg_color), self, "选择背景颜色")
        if color.isValid():
            self.current_bg_color = color.name()
            self.update_color_button(self.bg_color_btn, self.current_bg_color)
            self.update_preview()
    
    def reset_color(self, color_type):
        """重置颜色为默认值"""
        if color_type == 'font':
            self.current_font_color = "#000000"  # 黑色
            self.update_color_button(self.font_color_btn, self.current_font_color)
        elif color_type == 'bg':
            self.current_bg_color = "#ffffff"  # 白色
            self.update_color_button(self.bg_color_btn, self.current_bg_color)
        self.update_preview()
    
    def restore_defaults(self):
        """恢复所有默认设置"""
        self.scale_slider.setValue(100)
        self.current_font_color = "#000000"
        self.current_bg_color = "#ffffff"
        self.font_family_combo.setCurrentText("Microsoft YaHei")
        self.font_size_spin.setValue(12)
        self.font_bold_cb.setChecked(False)
        self.font_italic_cb.setChecked(False)
        self.font_underline_cb.setChecked(False)
        self.update_color_button(self.font_color_btn, self.current_font_color)
        self.update_color_button(self.bg_color_btn, self.current_bg_color)
        self.update_preview()
    
    def update_preview(self):
        """更新预览效果"""
        font_family = self.font_family_combo.currentText()
        font_size = self.font_size_spin.value()
        font_weight = "bold" if self.font_bold_cb.isChecked() else "normal"
        font_style = "italic" if self.font_italic_cb.isChecked() else "normal"
        text_decoration = "underline" if self.font_underline_cb.isChecked() else "none"
        
        self.preview_text.setStyleSheet(f"""
            color: {self.current_font_color};
            background-color: {self.current_bg_color};
            font-family: {font_family};
            font-size: {font_size}px;
            font-weight: {font_weight};
            font-style: {font_style};
            text-decoration: {text_decoration};
            padding: 15px;
            border: 1px solid #ccc;
            border-radius: 4px;
            line-height: 1.5;
        """)

    def update_scale_label(self, value):
        """更新缩放标签"""
        self.scale_label.setText(f"当前缩放: {value}%")

    def set_scale(self, value):
        """设置缩放值"""
        self.scale_slider.setValue(value)

    def get_scale(self):
        """获取缩放值"""
        return self.scale_slider.value()
    
    def get_font_color(self):
        """获取字体颜色"""
        return self.current_font_color
    
    def get_bg_color(self):
        """获取背景颜色"""
        return self.current_bg_color
    
    def get_font_family(self):
        """获取字体类型"""
        return self.font_family_combo.currentText()
    
    def get_font_size(self):
        """获取字体大小"""
        return self.font_size_spin.value()
    
    def get_font_bold(self):
        """获取字体加粗"""
        return self.font_bold_cb.isChecked()
    
    def get_font_italic(self):
        """获取字体斜体"""
        return self.font_italic_cb.isChecked()
    
    def get_font_underline(self):
        """获取字体下划线"""
        return self.font_underline_cb.isChecked()
    
    def get_use_system_theme(self):
        """获取系统主题跟随设置"""
        return self.use_system_theme_cb.isChecked()
    
    def on_system_theme_toggled(self, checked):
        """系统主题选项变化时触发"""
        self.update_preview()

    def save_settings(self):
        """保存设置"""
        scale = self.get_scale()
        font_color = self.get_font_color()
        bg_color = self.get_bg_color()
        font_family = self.get_font_family()
        font_size = self.get_font_size()
        font_bold = self.get_font_bold()
        font_italic = self.get_font_italic()
        font_underline = self.get_font_underline()
        
        self.settings.setValue("display_scale", scale)
        self.settings.setValue("font_color", font_color)
        self.settings.setValue("background_color", bg_color)
        self.settings.setValue("font_family", font_family)
        self.settings.setValue("font_size", font_size)
        self.settings.setValue("font_bold", font_bold)
        self.settings.setValue("font_italic", font_italic)
        self.settings.setValue("font_underline", font_underline)
        self.settings.setValue("use_system_theme", self.get_use_system_theme())
        self.settings.sync()
        
        return scale, font_color, bg_color, font_family, font_size, font_bold, font_italic, font_underline


# FarmIdUnificationDialog class removed - no longer needed for single-farm uploads
    


# BatchFarmIdInputDialog class removed - no longer needed for single-farm uploads


class EnhancedProgressDialog(QProgressDialog):
    """增强版进度条对话框，支持平滑动画和剩余时间估算"""
    
    def __init__(self, title, cancel_text, min_val, max_val, parent=None):
        super().__init__(title, cancel_text, min_val, max_val, parent)
        self.setWindowTitle("处理中")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setAutoClose(True)
        self.setAutoReset(True)
        
        # 初始化时间跟踪
        self.start_time = QDateTime.currentDateTime()
        self.last_update_time = self.start_time
        self.progress_history = []  # 存储(时间, 进度)元组用于计算速度
        
        # 创建自定义进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setBar(self.progress_bar)
        
        # 设置样式
        self.setStyleSheet("""
            QProgressDialog {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
            QProgressBar {
                border: 2px solid #0d6efd;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                background-color: #e9ecef;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #0d6efd, stop: 0.5 #0a58ca, stop: 1 #0d6efd);
                border-radius: 3px;
            }
            QLabel {
                color: #212529;
                font-size: 14px;
                font-weight: 500;
                margin: 10px 0;
            }
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #bb2d3b;
            }
        """)
        
        # 创建动画
        self._animation_value = 0
        self.animation = QPropertyAnimation(self, b"animationValue")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(500)  # 500ms的平滑过渡
        
        # 添加剩余时间标签
        self.time_label = QLabel("计算剩余时间...")
        self.setLabel(self.time_label)
        
        # 动画计时器
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(30)  # 30ms更新一次，确保流畅
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(150)
    
    def get_animationValue(self):
        return self._animation_value
    
    def set_animationValue(self, value):
        self._animation_value = value
        self.setValue(int(value))
    
    animationValue = pyqtProperty(float, get_animationValue, set_animationValue)
    
    def set_smooth_value(self, value):
        """平滑地设置进度值"""
        # 记录进度历史
        current_time = QDateTime.currentDateTime()
        self.progress_history.append((current_time, value))
        
        # 只保留最近10个记录
        if len(self.progress_history) > 10:
            self.progress_history.pop(0)
        
        # 更新剩余时间估算
        self.update_time_estimate(value)
        
        # 启动平滑动画
        self.animation.stop()
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.start()
    
    def update_time_estimate(self, current_value):
        """更新剩余时间估算"""
        if current_value <= 0 or current_value >= self.maximum():
            self.time_label.setText("处理完成" if current_value >= self.maximum() else "准备中...")
            return
        
        # 计算已用时间
        elapsed_ms = self.start_time.msecsTo(QDateTime.currentDateTime())
        
        # 如果有足够的历史数据，计算平均速度
        if len(self.progress_history) >= 2:
            # 使用最近的数据计算速度
            recent_time, recent_progress = self.progress_history[-1]
            old_time, old_progress = self.progress_history[0]
            
            time_diff_ms = old_time.msecsTo(recent_time)
            progress_diff = recent_progress - old_progress
            
            if progress_diff > 0 and time_diff_ms > 0:
                # 计算速度（进度/毫秒）
                speed = progress_diff / time_diff_ms
                
                # 计算剩余进度
                remaining_progress = self.maximum() - current_value
                
                # 估算剩余时间
                remaining_ms = int(remaining_progress / speed)
                
                # 格式化时间显示
                remaining_text = self.format_time(remaining_ms)
                elapsed_text = self.format_time(elapsed_ms)
                
                self.time_label.setText(
                    f"已用时间: {elapsed_text} | 预计剩余: {remaining_text}"
                )
            else:
                self.time_label.setText(f"已用时间: {self.format_time(elapsed_ms)}")
        else:
            self.time_label.setText(f"已用时间: {self.format_time(elapsed_ms)}")
    
    def format_time(self, milliseconds):
        """格式化时间显示"""
        seconds = milliseconds // 1000
        
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分"
    
    def update_animation(self):
        """更新动画效果"""
        # 可以在这里添加额外的视觉效果
        pass
    
    def set_label_text(self, text):
        """设置标签文本同时保留时间信息"""
        current_time_info = self.time_label.text()
        if "已用时间" in current_time_info:
            self.time_label.setText(f"{text}\n{current_time_info}")
        else:
            self.time_label.setText(text)


class FileProcessThread(QThread):
    """文件处理线程"""
    progress_updated = pyqtSignal(str, int)  # 状态信息, 进度百分比
    file_processed = pyqtSignal(str, bool, str, dict)  # 文件名, 成功, 消息, 数据信息
    processing_completed = pyqtSignal(dict)  # 完成信息
    log_updated = pyqtSignal(str)  # 处理过程日志
    
    def __init__(self, file_paths, filenames, urea_tracker=None):
        super().__init__()
        self.file_paths = file_paths
        self.filenames = filenames
        self.processor = DataProcessor()
        self.urea_tracker = urea_tracker
        
    def run(self):
        """运行文件处理"""
        try:
            from datetime import datetime
            
            total_files = len(self.filenames)
            self.log_updated.emit(f"📂 开始处理 {total_files} 个文件")
            self.log_updated.emit(f"⏰ 处理开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.progress_updated.emit("开始处理文件...", 5)
            
            # 逐个处理文件，提供更详细的进度
            success_files = []
            failed_files = []
            all_data = []
            farm_ids = set()
            
            for i, (file_path, filename) in enumerate(zip(self.file_paths, self.filenames)):
                base_progress = 10 + int((i / total_files) * 70)  # 10-80% for file processing
                
                self.log_updated.emit(f"\n📄 正在处理文件 {i+1}/{total_files}: {filename}")
                self.progress_updated.emit(f"处理文件 {i+1}/{total_files}: {filename}", base_progress)
                
                # 细分进度：读取文件
                self.progress_updated.emit(f"正在读取: {filename}", base_progress + 2)
                
                try:
                    # 如果文件很大，添加更多进度更新
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    if file_size > 10:
                        self.progress_updated.emit(f"正在解析大文件: {filename} ({file_size:.1f}MB)", base_progress + 5)
                    
                    success, message, df = self.processor.process_uploaded_file(file_path, filename)
                    
                    if success and df is not None:
                        # 获取数据信息
                        row_count = len(df)
                        date_range = self.processor.extract_date_range_from_data(df)
                        
                        # 提取牛场编号
                        if 'farm_id' in df.columns:
                            file_farm_ids = df['farm_id'].dropna().unique()
                            farm_ids.update(file_farm_ids)
                            self.log_updated.emit(f"   ✅ 成功: {row_count}行数据，牛场编号: {list(file_farm_ids)}")
                        else:
                            self.log_updated.emit(f"   ✅ 成功: {row_count}行数据，缺少牛场编号")
                        
                        if date_range:
                            self.log_updated.emit(f"   📅 数据时间范围: {date_range}")
                        
                        success_files.append({
                            'filename': filename,
                            'message': message,
                            'row_count': row_count,
                            'date_range': date_range
                        })
                        
                        all_data.append({
                            'filename': filename,
                            'data': df
                        })
                        
                        # 添加数据到尿素氮追踪器
                        if self.urea_tracker and date_range:
                            # 从日期范围中提取年月
                            try:
                                # date_range['year_month_range'] 格式如 "2024年1月 - 2024年3月"
                                year_month_str = date_range.get('year_month_range', '')
                                if ' - ' in year_month_str:
                                    # 取第一个月份作为数据的代表月份
                                    first_month = year_month_str.split(' - ')[0]
                                    # 转换为 YYYY-MM 格式
                                    import re
                                    match = re.match(r'(\d{4})年(\d{1,2})月', first_month)
                                    if match:
                                        year = match.group(1)
                                        month = match.group(2).zfill(2)
                                        date_str = f"{year}-{month}"
                                        self.urea_tracker.add_dhi_data(df, date_str)
                                        self.log_updated.emit(f"   🧪 已添加到尿素氮追踪: {date_str}")
                                else:
                                    # 单月数据
                                    match = re.match(r'(\d{4})年(\d{1,2})月', year_month_str)
                                    if match:
                                        year = match.group(1)
                                        month = match.group(2).zfill(2)
                                        date_str = f"{year}-{month}"
                                        self.urea_tracker.add_dhi_data(df, date_str)
                                        self.log_updated.emit(f"   🧪 已添加到尿素氮追踪: {date_str}")
                            except Exception as e:
                                self.log_updated.emit(f"   ⚠️ 尿素氮数据添加失败: {str(e)}")
                    else:
                        self.log_updated.emit(f"   ❌ 失败: {message}")
                        failed_files.append({
                            'filename': filename,
                            'error': message
                        })
                    
                    # 发送单个文件处理结果
                    file_info = {
                        'filename': filename,
                        'row_count': len(df) if df is not None else 0,
                        'date_range': date_range if success else None
                    }
                    
                    if success and df is not None and hasattr(df, 'attrs') and 'missing_farm_id_info' in df.attrs:
                        file_info['missing_farm_id_info'] = df.attrs['missing_farm_id_info']
                    
                    self.file_processed.emit(filename, success, message, file_info)
                    
                except Exception as e:
                    error_msg = f"处理失败: {str(e)}"
                    self.log_updated.emit(f"   ❌ 异常: {error_msg}")
                    failed_files.append({
                        'filename': filename,
                        'error': error_msg
                    })
                    self.file_processed.emit(filename, False, error_msg, {})
            
            self.progress_updated.emit("汇总处理结果...", 85)
                    
                    # 收集缺少管理号的文件信息
            missing_farm_id_files = []
            for data_item in all_data:
                df = data_item['data']
                if hasattr(df, 'attrs') and 'missing_farm_id_info' in df.attrs:
                    missing_info = df.attrs['missing_farm_id_info']
                    source_info = self._get_source_info(data_item['filename'])
                    missing_farm_id_files.append({
                        'filename': data_item['filename'],
                        'missing_info': missing_info,
                        'source_info': source_info,
                        'data': df
                    })
            
            # 汇总结果
            results = {
                'success_files': success_files,
                'failed_files': failed_files,
                'all_data': all_data,
                'farm_ids': sorted(list(farm_ids)),
                'missing_farm_id_files': missing_farm_id_files
            }
            
            self.progress_updated.emit("文件处理完成", 100)
            self.log_updated.emit(f"\n📊 处理完成统计:")
            self.log_updated.emit(f"   ✅ 成功: {len(success_files)} 个文件")
            self.log_updated.emit(f"   ❌ 失败: {len(failed_files)} 个文件")
            self.log_updated.emit(f"   🏢 发现牛场: {len(farm_ids)} 个")
            if missing_farm_id_files:
                self.log_updated.emit(f"   ⚠️ 缺少管理号: {len(missing_farm_id_files)} 个文件")
            self.log_updated.emit(f"⏰ 处理完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            self.processing_completed.emit(results)
            
        except Exception as e:
            error_msg = f"处理过程出现严重错误: {str(e)}"
            self.log_updated.emit(f"\n❌ {error_msg}")
            import traceback
            self.log_updated.emit(f"错误详情:\n{traceback.format_exc()}")
            
            # 发送错误信号给所有文件
            for filename in self.filenames:
                self.file_processed.emit(filename, False, error_msg, {})

    def _get_source_info(self, filename):
        """获取文件来源信息"""
        # 检查是否来自压缩包
        for file_path in self.file_paths:
            if filename in file_path:
                if '.zip' in file_path.lower():
                    # 从压缩包中提取的文件
                    zip_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                    return f"压缩包: {zip_name}"
                else:
                    # 单独上传的文件
                    return "单独上传"
        
        return "单独上传"


class FilterThread(QThread):
    """筛选处理线程"""
    progress_updated = pyqtSignal(str, int)
    filtering_completed = pyqtSignal(bool, str, pd.DataFrame, dict)  # 添加统计信息字典
    log_updated = pyqtSignal(str)  # 筛选过程日志
    
    def __init__(self, data_list, filters, selected_files, processor=None, urea_tracker=None):
        super().__init__()
        self.data_list = data_list
        self.filters = filters
        self.selected_files = selected_files
        self.processor = processor if processor else DataProcessor()
        self.urea_tracker = urea_tracker
        self._should_stop = False  # 停止标志
    
    def stop(self):
        """停止筛选"""
        self._should_stop = True
        self.log_updated.emit("⏹️ 用户请求停止筛选...")
    
    def request_cancel(self):
        """请求取消（别名）"""
        self.stop()
    
    def should_stop(self):
        """检查是否应该停止"""
        return self._should_stop
    
    def run(self):
        """执行筛选"""
        try:
            from datetime import datetime, timedelta
            
            self.log_updated.emit(f"\n🔍 开始筛选数据")
            self.log_updated.emit(f"⏰ 筛选开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.progress_updated.emit("开始筛选...", 5)
            
            # 统计启用的筛选项
            enabled_filters = []
            for filter_name, filter_config in self.filters.items():
                if filter_config.get('enabled', False) and filter_name not in ['parity', 'date_range']:
                    enabled_filters.append(filter_name)
            
            self.log_updated.emit(f"📋 启用的筛选项: {enabled_filters if enabled_filters else '仅基础筛选'}")
            
            self.progress_updated.emit("统计数据规模...", 10)
            
            # 计算全部数据的牛头数
            all_cows = set()
            for item in self.data_list:
                df = item['data']
                if 'management_id' in df.columns:
                    cow_ids = df['management_id'].dropna().unique()
                    for cow_id in cow_ids:
                        all_cows.add(cow_id)
            
            self.log_updated.emit(f"📊 全部数据: {len(all_cows)} 头牛")
            
            # 计算筛选范围的牛头数
            range_cows = set()
            selected_data = [item for item in self.data_list if item['filename'] in self.selected_files]
            for item in selected_data:
                df = item['data']
                if 'management_id' in df.columns:
                    cow_ids = df['management_id'].dropna().unique()
                    for cow_id in cow_ids:
                        range_cows.add(cow_id)
            
            self.log_updated.emit(f"📊 筛选范围: {len(range_cows)} 头牛 (来自{len(self.selected_files)}个文件)")
            
            self.progress_updated.emit("应用筛选条件...", 25)
            
            # 使用新的多筛选项逻辑
            self.log_updated.emit(f"🔧 开始应用多筛选项逻辑...")
            
            def progress_callback(message, progress):
                """进度回调函数"""
                self.progress_updated.emit(message, progress)
                self.log_updated.emit(f"   {message}")
            
            filtered_df = self.processor.apply_multi_filter_logic(
                self.data_list, self.filters, self.selected_files,
                progress_callback=progress_callback, should_stop=self.should_stop
            )
            
            # 检查是否被停止
            if self._should_stop:
                self.log_updated.emit("❌ 筛选已被用户取消")
                self.filtering_completed.emit(False, "筛选已被用户取消", pd.DataFrame(), {})
                return
            
            basic_filter_count = len(filtered_df)
            self.log_updated.emit(f"📊 基础筛选后: {basic_filter_count} 条记录")
            
            self.progress_updated.emit("生成月度报告...", 50)
            
            # 动态构建display_fields，包含所有启用的筛选项
            display_fields = ['management_id', 'parity']
            
            # 添加启用的筛选项到display_fields
            # 定义所有支持的字段
            supported_fields = [
                'protein_pct', 'fat_pct', 'fat_protein_ratio', 'somatic_cell_count', 
                'somatic_cell_score', 'urea_nitrogen', 'lactose_pct', 'milk_loss',
                'milk_payment_diff', 'economic_loss', 'corrected_milk', 'persistency',
                'whi', 'fore_milk_yield', 'fore_somatic_cell_count', 'fore_somatic_cell_score',
                'fore_milk_loss', 'peak_milk_yield', 'peak_days', 'milk_305',
                'total_milk_yield', 'total_fat_pct', 'total_protein_pct', 'mature_equivalent'
            ]
            
            for filter_name in enabled_filters:
                if filter_name in supported_fields:
                    display_fields.append(filter_name)
            
            # 确保包含必要的字段 - 任何性状筛选都需要泌乳天数和产奶量
            if 'lactation_days' not in display_fields:
                display_fields.append('lactation_days')
            
            if 'milk_yield' not in display_fields:
                display_fields.append('milk_yield')
            
            self.log_updated.emit(f"📋 生成月度报告，包含字段: {display_fields}")
            
            # 总是获取计划调群日期，用于计算未来泌乳天数（无论是否启用筛选）
            plan_date = None
            if 'future_lactation_days' in self.filters:
                plan_date = self.filters['future_lactation_days'].get('plan_date')
            
            # 如果未设置，使用默认值（当前日期+30天）
            if not plan_date:
                default_plan_date = datetime.now() + timedelta(days=30)
                plan_date = default_plan_date.strftime('%Y-%m-%d')
            
            self.log_updated.emit(f"📅 计划调群日期: {plan_date}")
            
            monthly_report = self.processor.create_monthly_report(filtered_df, display_fields, plan_date)
            
            self.log_updated.emit(f"📊 月度报告生成: {len(monthly_report)} 条记录")
            
                        # 如果启用了未来泌乳天数筛选，对月度报告进行最后的筛选
            if 'future_lactation_days' in self.filters and self.filters['future_lactation_days'].get('enabled', False):
                self.progress_updated.emit("应用未来泌乳天数筛选...", 75)
                future_filter = self.filters['future_lactation_days']
                before_future_count = len(monthly_report)
                
                self.log_updated.emit(f"🔮 应用未来泌乳天数筛选: {future_filter['min']}-{future_filter['max']}天")
                
                # 对月度报告进行未来泌乳天数筛选
                if not monthly_report.empty and '未来泌乳天数(天)' in monthly_report.columns:
                    monthly_report = self.processor.apply_numeric_filter(monthly_report, '未来泌乳天数(天)', future_filter)
                    
                after_future_count = len(monthly_report)
                self.log_updated.emit(f"📊 未来泌乳天数筛选后: {after_future_count} 条记录 (筛除{before_future_count - after_future_count}条)")
            
            # 应用在群牛筛选（最后一步）
            if self.processor.active_cattle_enabled:
                self.progress_updated.emit("应用在群牛筛选...", 90)
                before_active_count = len(monthly_report)
                
                cattle_count = len(self.processor.active_cattle_list) if self.processor.active_cattle_list else 0
                self.log_updated.emit(f"🐄 应用在群牛筛选 (在群牛清单: {cattle_count}头)")
                monthly_report = self.processor.apply_active_cattle_filter(monthly_report)
                
                after_active_count = len(monthly_report)
                self.log_updated.emit(f"📊 在群牛筛选后: {after_active_count} 条记录 (筛除{before_active_count - after_active_count}条)")
            
            # 计算筛选结果的牛头数
            result_cows = set()
            if not monthly_report.empty and 'management_id' in monthly_report.columns:
                cow_ids = monthly_report['management_id'].dropna().unique()
                for cow_id in cow_ids:
                    result_cows.add(cow_id)
            
            # 计算筛选率
            filter_rate = (len(result_cows) / len(all_cows) * 100) if len(all_cows) > 0 else 0
            
            # 构建统计信息
            stats = {
                'total_cows': len(all_cows),
                'range_cows': len(range_cows), 
                'result_cows': len(result_cows),
                'filter_rate': filter_rate,
                'active_cattle_enabled': self.processor.active_cattle_enabled,
                'active_cattle_count': len(self.processor.active_cattle_list) if self.processor.active_cattle_list else 0
            }
            
            # 尿素氮追踪分析
            urea_tracking_config = self.filters.get('urea_tracking', {})
            if urea_tracking_config.get('enabled', False) and self.urea_tracker:
                self.progress_updated.emit("执行尿素氮追踪分析...", 95)
                self.log_updated.emit("\n🧪 执行尿素氮追踪分析...")
                
                urea_results = self.urea_tracker.analyze(
                    selected_groups=urea_tracking_config['selected_groups'],
                    filter_outliers=urea_tracking_config['filter_outliers'],
                    min_value=urea_tracking_config['min_value'],
                    max_value=urea_tracking_config['max_value'],
                    min_sample_size=urea_tracking_config['min_sample_size']
                )
                
                if 'error' not in urea_results:
                    stats['urea_tracking'] = {
                        'results': urea_results,
                        'value_type': urea_tracking_config['value_type']
                    }
                    group_count = len(urea_results)
                    total_history_points = sum(len(group['history']) for group in urea_results.values())
                    self.log_updated.emit(f"   ✅ 尿素氮分析完成: {group_count}个组，{total_history_points}个历史数据点")
                else:
                    self.log_updated.emit(f"   ❌ 尿素氮分析失败: {urea_results['error']}")
            
            self.progress_updated.emit("筛选完成", 100)
            
            self.log_updated.emit(f"\n✅ 筛选完成统计:")
            self.log_updated.emit(f"   📊 最终结果: {len(result_cows)} 头牛，{len(monthly_report)} 条记录")
            self.log_updated.emit(f"   📈 筛选率: {filter_rate:.1f}%")
            if self.processor.active_cattle_enabled:
                self.log_updated.emit(f"   🐄 已应用在群牛筛选")
            self.log_updated.emit(f"⏰ 筛选完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            success_msg = f"筛选完成，共筛选出 {len(result_cows)} 头牛，{len(monthly_report)} 条记录"
            if self.processor.active_cattle_enabled:
                success_msg += f"（已应用在群牛筛选）"
            
            self.filtering_completed.emit(True, success_msg, monthly_report, stats)
            
        except Exception as e:
            error_msg = f"筛选失败: {str(e)}"
            self.log_updated.emit(f"\n❌ {error_msg}")
            import traceback
            self.log_updated.emit(f"错误详情:\n{traceback.format_exc()}")
            self.filtering_completed.emit(False, error_msg, pd.DataFrame(), {})


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, username=None, auth_service=None):
        super().__init__()
        self.username = username or "未登录用户"
        self.auth_service = auth_service
        self.data_list = []  # 存储所有处理过的数据
        self.processor = DataProcessor()
        self.data_processor = self.processor  # 为慢性乳房炎筛查功能提供别名
        self.current_results = pd.DataFrame()  # 当前筛选结果
        self.heartbeat_timer = None  # 心跳定时器
        
        # 初始化尿素氮追踪器
        from urea_tracker import UreaTracker
        self.urea_tracker = UreaTracker()
        self.urea_tracking_results = None
        
        # 加载显示设置
        self.settings = QSettings("DHI", "ProteinScreening")
        self.display_scale = self.settings.value("display_scale", 100, type=int)
        
        # 防呆设计：检查字体颜色是否过浅，自动修正
        raw_font_color = self.settings.value("font_color", "#000000", type=str)
        self.font_color = self.validate_and_fix_font_color(raw_font_color)
        
        self.background_color = self.settings.value("background_color", "#ffffff", type=str)
        self.font_family = self.settings.value("font_family", "Microsoft YaHei", type=str)
        self.font_size = self.settings.value("font_size", 12, type=int)
        self.font_bold = self.settings.value("font_bold", False, type=bool)
        self.font_italic = self.settings.value("font_italic", False, type=bool)
        self.font_underline = self.settings.value("font_underline", False, type=bool)
        
        # 初始化筛选相关变量
        self.added_other_filters = {}  # 存储添加的其他筛选项
        self.dhi_processed_ok = False  # 基础数据是否已处理完毕标志
        
        self.init_ui()
        self.load_config()
        
        # 启动时检查是否有显示问题（防呆功能）
        QTimer.singleShot(1000, self.check_display_issues_on_startup)
        
        # 启动心跳机制
        if self.auth_service:
            self.start_heartbeat()
    
    def validate_and_fix_font_color(self, color_str: str) -> str:
        """防呆设计：验证并修正字体颜色，防止设置过浅的颜色导致文字不可见"""
        try:
            # 移除#号
            hex_color = color_str.lstrip('#')
            if len(hex_color) != 6:
                return "#000000"  # 无效格式，返回黑色
            
            # 转换为RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
            
            # 计算亮度（使用相对亮度公式）
            brightness = (r * 0.299 + g * 0.587 + b * 0.114) / 255
            
            # 如果亮度过高（> 0.9），强制使用黑色
            if brightness > 0.9:
                print(f"⚠️ 防呆提醒：检测到过浅的字体颜色 {color_str}（亮度{brightness:.1%}），已自动修正为黑色")
                # 同时更新设置中的值，避免下次启动再次触发
                self.settings.setValue("font_color", "#000000")
                return "#000000"
                
            # 颜色合适，返回原值
            return color_str
            
        except Exception as e:
            print(f"⚠️ 字体颜色验证出错 {color_str}: {e}，使用默认黑色")
            return "#000000"
    
    def get_safe_screen_info(self):
        """安全地获取屏幕信息 - 更准确的DPI适配"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return {
                'width': 1920,
                'height': 1080,
                'dpi_ratio': 1.0,
                'logical_dpi': 96.0,
                'physical_dpi': 96.0,
                'scale_factor': 1.0
            }
        else:
            geometry = screen.availableGeometry()
            logical_dpi = screen.logicalDotsPerInch()
            physical_dpi = screen.physicalDotsPerInch()
            device_pixel_ratio = screen.devicePixelRatio()
            
            # 计算系统缩放比例 - 更准确的方法
            system_scale_factor = logical_dpi / 96.0  # Windows标准DPI
            
            return {
                'width': geometry.width(),
                'height': geometry.height(),
                'dpi_ratio': device_pixel_ratio,
                'logical_dpi': logical_dpi,
                'physical_dpi': physical_dpi,
                'scale_factor': system_scale_factor
            }
    
    def safe_show_status_message(self, message: str):
        """安全地显示状态栏消息"""
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(message)
    
    def get_dpi_scaled_size(self, base_size: int) -> int:
        """根据系统DPI设置计算适配后的尺寸"""
        screen_info = self.get_safe_screen_info()
        
        # 使用系统缩放比例和用户自定义缩放的组合
        system_scale = screen_info['scale_factor']
        user_scale = self.display_scale / 100.0
        
        # 最终缩放比例 = 系统缩放 × 用户缩放
        final_scale = system_scale * user_scale
        
        # 应用缩放并确保最小值
        scaled_size = max(int(base_size * final_scale), base_size // 2)
        
        return scaled_size
    
    def get_dpi_scaled_font_size(self, base_font_size: int) -> int:
        """根据系统DPI设置计算适配后的字体大小"""
        return self.get_dpi_scaled_size(base_font_size)
    
    def detect_system_theme(self):
        """检测系统主题（深色/浅色模式）"""
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                import subprocess
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"], 
                    capture_output=True, text=True
                )
                return "dark" if result.stdout.strip() == "Dark" else "light"
            elif system == "Windows":
                try:
                    import winreg
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                    winreg.CloseKey(key)
                    return "light" if value else "dark"
                except:
                    return "light"
            else:  # Linux等
                return "light"
        except:
            return "light"
    
    def get_system_theme_colors(self):
        """根据系统主题获取适当的颜色"""
        theme = self.detect_system_theme()
        
        if theme == "dark":
            return {
                'background': '#2b2b2b',
                'surface': '#3c3c3c', 
                'text': '#ffffff',
                'text_secondary': '#b0b0b0',
                'border': '#555555',
                'accent': '#0084ff',
                'card_bg': '#404040',
                'input_bg': '#353535'
            }
        else:
            return {
                'background': '#f8f9fa',
                'surface': '#ffffff',
                'text': '#000000', 
                'text_secondary': '#6c757d',
                'border': '#dee2e6',
                'accent': '#007bff',
                'card_bg': '#ffffff',
                'input_bg': '#ffffff'
                         }
    
    def apply_consistent_styling(self):
        """应用统一的字体大小和系统主题跟随样式"""
        # 检测是否应该使用系统主题
        use_system_theme = self.settings.value("use_system_theme", True, type=bool)
        
        if use_system_theme:
            # 使用系统主题
            theme_colors = self.get_system_theme_colors()
            font_color = theme_colors['text']
            background_color = theme_colors['input_bg']
            card_bg = theme_colors['card_bg']
            border_color = theme_colors['border']
            accent_color = theme_colors['accent']
        else:
            # 使用用户自定义颜色
            font_color = self.font_color
            background_color = self.background_color
            card_bg = "#ffffff"
            border_color = "#dee2e6"
            accent_color = "#007bff"
        
        # 统一的基础字体大小 - 所有控件使用相同大小
        base_font_size = self.get_dpi_scaled_font_size(self.font_size)
        
        # 构建字体样式字符串
        font_weight = "bold" if self.font_bold else "normal"
        font_style = "italic" if self.font_italic else "normal"
        text_decoration = "underline" if self.font_underline else "none"
        
        # 应用全局样式 - 确保所有控件字体大小完全统一
        self.setStyleSheet(f"""
            /* 全局字体设置 - 强制所有控件使用统一字体大小 */
            * {{
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-size: {base_font_size}px !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            
            QMainWindow {{
                background-color: {theme_colors.get('background', '#f8f9fa') if use_system_theme else '#f8f9fa'};
                color: {font_color};
            }}
            
            QWidget {{
                color: {font_color};
                background-color: transparent;
            }}
            
            /* 输入控件 */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
                color: black;
                background-color: white;
                border: 1px solid {border_color};
                padding: 6px;
                border-radius: 4px;
                font-weight: bold;
            }}
            
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, 
            QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {accent_color};
                color: black;
            }}
            
            /* 文本显示控件 */
            QLabel {{
                color: black;
                background-color: white;
                text-decoration: {text_decoration};
                font-weight: bold;
            }}
            
            /* 按钮 */
            QPushButton {{
                color: {font_color};
                background-color: #e9ecef;
                border: 1px solid {border_color};
                padding: 8px 16px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: #dee2e6;
            }}
            
            QPushButton:pressed {{
                background-color: #d3d9df;
            }}
            
            QPushButton:disabled {{
                background-color: #f8f9fa;
                color: #6c757d;
            }}
            
            /* 复选框和单选按钮 */
            QCheckBox, QRadioButton {{
                color: black;
                background-color: white;
                spacing: 6px;
                font-weight: bold;
            }}
            
            /* 复选框和单选框不需要选中时的背景 */
            
            QCheckBox::indicator, QRadioButton::indicator {{
                width: {self.get_dpi_scaled_size(16)}px;
                height: {self.get_dpi_scaled_size(16)}px;
                background-color: white;
                border: 2px solid #666666;
            }}
            
            QCheckBox::indicator {{
                border-radius: 3px;
            }}
            
            QRadioButton::indicator {{
                border-radius: {self.get_dpi_scaled_size(8)}px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {accent_color};
                border: 2px solid {accent_color};
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTkgMTYuMTdMNC44MyAxMmwtMS40MiAxLjQxTDkgMTkgMjEgN2wtMS40MS0xLjQxeiIvPjwvc3ZnPg==);
            }}
            
            QRadioButton::indicator:checked {{
                background-color: {accent_color};
                border: 2px solid {accent_color};
            }}
            
            QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
                border-color: {accent_color};
            }}
            
            /* 表格 */
            QTableWidget {{
                color: black;  /* 强制使用黑色字体 */
                background-color: white;  /* 强制使用白色背景 */
                gridline-color: {border_color};
                selection-background-color: {accent_color}40;
            }}
            
            QTableWidget::item {{
                color: black;  /* 强制使用黑色字体 */
                background-color: white;  /* 强制使用白色背景 */
                padding: 4px;
                border: none;
            }}
            
            QHeaderView::section {{
                color: {font_color};
                background-color: {card_bg};
                border: 1px solid {border_color};
                padding: 6px;
                font-weight: bold;
            }}
            
            /* 文本编辑器 */
            QTextEdit {{
                color: {font_color};
                background-color: {background_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 8px;
            }}
            
            /* 分组框 */
            QGroupBox {{
                color: {font_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                margin-top: 10px;
                background-color: transparent;
            }}
            
            QGroupBox::title {{
                color: {font_color};
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: {theme_colors.get('background', '#f8f9fa') if use_system_theme else '#f8f9fa'};
            }}
            
            /* 标签页 */
            QTabWidget::pane {{
                border: 1px solid {border_color};
                border-radius: 4px;
                background-color: {card_bg};
            }}
            
            QTabBar::tab {{
                color: {font_color};
                background-color: {card_bg};
                border: 1px solid {border_color};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {card_bg};
                border-bottom: 2px solid {accent_color};
                color: {accent_color};
                font-weight: bold;
            }}
            
            QTabBar::tab:hover {{
                background-color: {border_color};
            }}
            
            /* 状态栏 */
            QStatusBar {{
                background-color: {theme_colors.get('background', '#f8f9fa') if use_system_theme else '#f8f9fa'};
                color: {font_color};
                border-top: 1px solid {border_color};
                padding: 4px;
            }}
            
            /* 菜单栏 */
            QMenuBar {{
                background-color: {theme_colors.get('background', '#f8f9fa') if use_system_theme else '#f8f9fa'};
                color: {font_color};
                border-bottom: 1px solid {border_color};
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {border_color};
            }}
            
            QMenu {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            
            QMenu::item {{
                padding: 6px 12px;
            }}
            
            QMenu::item:selected {{
                background-color: {border_color};
            }}
            
            /* 进度条 */
            QProgressBar {{
                background-color: {background_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                color: {font_color};
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {accent_color};
                border-radius: 3px;
            }}
            
            /* 工具提示 */
            QToolTip {{
                background-color: {card_bg};
                color: {font_color};
                border: 1px solid {border_color};
                padding: 4px;
                border-radius: 4px;
            }}
        """)
    
    def force_uniform_font_on_all_widgets(self):
        """遍历所有控件，强制设置统一的字体大小（最终保险措施）"""
        try:
            base_font_size = self.get_dpi_scaled_font_size(self.font_size)
            
            # 创建统一的字体对象
            uniform_font = QFont(self.font_family)
            uniform_font.setPointSize(base_font_size)
            uniform_font.setBold(self.font_bold)
            uniform_font.setItalic(self.font_italic)
            uniform_font.setUnderline(self.font_underline)
            
            def apply_font_to_widget(widget):
                if widget is None:
                    return
                
                try:
                    # 设置字体
                    widget.setFont(uniform_font)
                    
                    # 递归处理所有子控件
                    for child in widget.findChildren(QWidget):
                        child.setFont(uniform_font)
                        
                except Exception as e:
                    # 忽略无法设置字体的控件
                    pass
            
            # 从主窗口开始遍历
            apply_font_to_widget(self)
            
            print(f"✅ 字体统一完成：所有控件已设置为 {self.font_family} {base_font_size}px")
            
        except Exception as e:
            print(f"⚠️ 字体统一过程中出现错误: {e}")

     
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("DHI筛查助手 - 伊利液奶奶科院")
        
        # 设置全局样式 - 确保所有复选框、单选框、输入框有良好的对比度
        self.setStyleSheet("""
            QCheckBox {
                color: black;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: white;
                border: 2px solid #666;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #007AFF;
                border-color: #007AFF;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTkgMTYuMTdMNC44MyAxMmwtMS40MiAxLjQxTDkgMTkgMjEgN2wtMS40MS0xLjQxeiIvPjwvc3ZnPg==);
            }
            /* 复选框不需要选中时的背景 */
            QCheckBox::indicator:hover {
                border-color: #007AFF;
            }
            QRadioButton {
                color: black;
                background-color: transparent;
            }
            /* 单选框不需要选中时的背景 */
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                background-color: white;
                border: 2px solid #666;
                border-radius: 8px;
            }
            QRadioButton::indicator:checked {
                background-color: #007AFF;
                border-color: #007AFF;
            }
            /* 移除after伪元素，使单选框完全填充 */
            QSpinBox, QDoubleSpinBox, QLineEdit {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                padding: 5px;
                border-radius: 3px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
                border-color: #007AFF;
            }
            QGroupBox {
                color: black;
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
                color: black;
            }
            QLabel {
                color: black;
                background-color: transparent;
            }
            /* 确保标签页内容区域背景为白色 */
            QTabWidget::pane {
                background-color: white;
            }
            QWidget {
                background-color: white;
            }
            /* 表格样式 */
            QTableWidget {
                background-color: white;
                color: black;
                gridline-color: #ddd;
                selection-background-color: #007AFF;
                selection-color: white;
            }
            QTableWidget::item {
                color: black;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #007AFF;
                color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: black;
                font-weight: bold;
                border: 1px solid #ddd;
                padding: 5px;
            }
            /* 按钮样式 - 确保良好对比度 */
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
            QPushButton:pressed {
                background-color: #0041AB;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            /* 特殊按钮样式保持原样 */
            QPushButton#enableCheckbox {
                background-color: transparent;
            }
        """)
        
        # 创建菜单栏 - 只创建一次
        self.create_menu_bar()
        
        # 自适应窗口大小 - 根据屏幕尺寸设置
        screen_info = self.get_safe_screen_info()
        screen_width = screen_info['width']
        screen_height = screen_info['height']
        
        # 设置窗口为屏幕的80%，但有最小和最大限制
        window_width = min(max(int(screen_width * 0.8), 1200), 1800)
        window_height = min(max(int(screen_height * 0.8), 800), 1200)
        
        # 窗口居中
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)
        
        # 设置最小尺寸
        self.setMinimumSize(1000, 700)
        
        # 设置图标
        try:
            if os.path.exists("whg3r-qi1nv-001.ico"):
                self.setWindowIcon(QIcon("whg3r-qi1nv-001.ico"))
        except:
            pass
        
        # 应用系统主题跟随和统一字体大小
        self.apply_consistent_styling()
        

        
        # 创建中央部件
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: #f8f9fa;")  # 主窗口保持灰色背景
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 添加顶部标题栏 - 高度相对于屏幕
        header = self.create_header()
        main_layout.addWidget(header)
        
        # 添加步骤指示器
        steps_widget = self.create_steps_indicator()
        main_layout.addWidget(steps_widget)
        
        # 创建可分割的内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setContentsMargins(10, 10, 10, 10)
        
        # ===========================================
        # 左侧控制面板 - 平衡滚动策略
        # ===========================================
        # 经过UI优化后的最终方案：保留滚动功能但设置合理高度
        # 
        # 设计考虑：
        # 1. 保留QScrollArea - 当内容过多时可以滚动，避免内容被截断
        # 2. 设置600px最小高度 - 确保主要内容在首屏可见
        # 3. 结合标签页内的顶部对齐设计，达到最佳用户体验
        left_scroll = QScrollArea()
        
        # 滚动区域基本设置
        left_scroll.setWidgetResizable(True)  # 内容自适应滚动区域大小
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 禁用横向滚动
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)     # 按需显示纵向滚动
        
        # 宽度限制 - 确保在不同屏幕上的适配性
        left_scroll.setMinimumWidth(400)  # 减小最小宽度到400px
        # 移除最大宽度限制，允许用户自由调整
        # left_scroll.setMaximumWidth(800)  # 注释掉最大宽度限制
        
        # 🎯 高度策略 - 平衡内容可见性和空间效率的关键设置
        left_scroll.setMinimumHeight(400)  # 降低到400px - 避免文件上传区域过度拉伸
        
        left_panel = self.create_control_panel()
        left_scroll.setWidget(left_panel)
        content_splitter.addWidget(left_scroll)
        
        # 右侧结果显示
        right_panel = self.create_result_panel()
        right_panel.setMinimumWidth(200)  # 减少右侧最小宽度限制，允许拖拽条更灵活
        content_splitter.addWidget(right_panel)
        
        # 设置分割器比例和约束 - 调整为4:6比例，给右侧更多空间
        left_width = max(450, int(window_width * 0.4))  # 左侧占40%，至少450px
        right_width = window_width - left_width
        content_splitter.setSizes([left_width, right_width])
        content_splitter.setCollapsible(0, False)
        content_splitter.setCollapsible(1, False)
        
        # 设置分割器样式 - 更明显的拖拽手柄
        content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #ced4da;
                width: 5px;
                margin: 1px;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #007bff;
                width: 7px;
            }
            QSplitter::handle:pressed {
                background-color: #0056b3;
            }
        """)
        
        main_layout.addWidget(content_splitter)
        
        # 状态栏
        self.setup_status_bar()
        
        # 强制统一所有控件的字体大小（最终保险措施）
        QTimer.singleShot(500, self.force_uniform_font_on_all_widgets)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        if menubar is None:
            return
        
        # 设置菜单栏样式 - 使用统一字体大小
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 4px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: #e9ecef;
            }}
            QMenu {{
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }}
            QMenu::item {{
                padding: 6px 12px;
            }}
            QMenu::item:selected {{
                background-color: #e9ecef;
            }}
        """)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        # 显示设置
        display_action = QAction("界面显示设置...", self)
        display_action.setStatusTip("调整界面显示比例")
        display_action.triggered.connect(self.show_display_settings)
        settings_menu.addAction(display_action)
        
        # 恢复默认显示（防呆功能）
        reset_display_action = QAction("🔧 恢复默认显示", self)
        reset_display_action.setStatusTip("一键恢复默认字体颜色和显示设置（解决文字看不见问题）")
        reset_display_action.triggered.connect(self.reset_display_settings_to_default)
        settings_menu.addAction(reset_display_action)
        
        settings_menu.addSeparator()
        
        # 关于
        about_action = QAction("关于", self)
        about_action.setStatusTip("关于DHI筛查助手")
        about_action.triggered.connect(self.show_about)
        settings_menu.addAction(about_action)
        
        # 账号菜单 - 已移除，功能集成到其他位置
        # account_menu = menubar.addMenu("账号")
        
        # # 当前用户显示
        # user_display = self.username
        # if self.auth_service and hasattr(self.auth_service, 'get_user_name'):
        #     full_name = self.auth_service.get_user_name()
        #     if full_name and full_name != self.username:
        #         user_display = f"{self.username} ({full_name})"
        
        # user_info_action = QAction(f"当前用户: {user_display}", self)
        # user_info_action.setEnabled(False)
        # account_menu.addAction(user_info_action)
        
        # account_menu.addSeparator()
        
        # # 修改密码
        # change_password_action = QAction("修改密码...", self)
        # change_password_action.setStatusTip("修改当前账号密码")
        # change_password_action.triggered.connect(self.show_change_password)
        # account_menu.addAction(change_password_action)
        
        # # 邀请码管理
        # invite_code_action = QAction("邀请码管理...", self)
        # invite_code_action.setStatusTip("管理系统邀请码")
        # invite_code_action.triggered.connect(self.show_invite_code_management)
        # account_menu.addAction(invite_code_action)
        
        # account_menu.addSeparator()
        
        # # 退出登录
        # logout_action = QAction("退出登录", self)
        # logout_action.setStatusTip("退出当前账号")
        # logout_action.triggered.connect(self.logout)
        # account_menu.addAction(logout_action)
    
    def show_display_settings(self):
        """显示界面设置对话框"""
        dialog = DisplaySettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_scale, new_font_color, new_bg_color, new_font_family, new_font_size, new_font_bold, new_font_italic, new_font_underline = dialog.save_settings()
            
            # 提示用户重启程序
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("设置已保存")
            msg.setText(f"显示设置已更新")
            msg.setInformativeText(f"显示比例: {new_scale}%\n字体颜色: {new_font_color}\n背景颜色: {new_bg_color}\n字体类型: {new_font_family}\n字体大小: {new_font_size}px\n字体加粗: {'是' if new_font_bold else '否'}\n字体斜体: {'是' if new_font_italic else '否'}\n下划线: {'是' if new_font_underline else '否'}\n\n建议重启程序以获得最佳显示效果。")
            
            restart_btn = msg.addButton("重启程序", QMessageBox.ButtonRole.AcceptRole)
            later_btn = msg.addButton("稍后重启", QMessageBox.ButtonRole.RejectRole)
            
            msg.exec()
            
            if msg.clickedButton() == restart_btn:
                self.restart_application()
            else:
                # 即时应用样式更新，无需重启
                # 重新加载设置
                self.display_scale = self.settings.value("display_scale", 100, type=int)
                self.font_color = self.settings.value("font_color", "#000000", type=str)
                self.background_color = self.settings.value("background_color", "#ffffff", type=str)
                self.font_family = self.settings.value("font_family", "Microsoft YaHei", type=str)
                self.font_size = self.settings.value("font_size", 12, type=int)
                self.font_bold = self.settings.value("font_bold", False, type=bool)
                self.font_italic = self.settings.value("font_italic", False, type=bool)
                self.font_underline = self.settings.value("font_underline", False, type=bool)
                
                # 应用新的样式
                self.apply_consistent_styling()
                
                # 强制统一所有控件的字体大小
                QTimer.singleShot(100, self.force_uniform_font_on_all_widgets)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于DHI筛查助手",
                          "DHI筛查助手 v3.0\n\n"
                         "伊利液奶奶科院\n"
                         "用于处理DHI报告数据的专业助手\n"
                         "支持批量文件处理和多种筛选条件\n"
                         "乳房炎筛查和监测分析功能\n\n"
                         "如有问题请联系技术支持")
    
    def restart_application(self):
        """重启应用程序"""
        import subprocess
        import sys
        
        QApplication.quit()
        subprocess.Popen([sys.executable] + sys.argv)
    
    def create_styled_message_box(self, icon_type, title, text, buttons=None, default_button=None):
        """创建带有统一样式的消息框"""
        msg = QMessageBox(self)
        msg.setIcon(icon_type)
        msg.setWindowTitle(title)
        msg.setText(text)
        
        # 设置统一的样式 - 确保文字清晰可见
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
                color: black;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                font-size: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            QMessageBox QLabel {
                color: black;
                background-color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 13px;
            }
            QMessageBox QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 60px;
            }
            QMessageBox QPushButton:hover {
                background-color: #0056b3;
            }
            QMessageBox QPushButton:pressed {
                background-color: #004085;
            }
            QMessageBox QPushButton:default {
                background-color: #28a745;
            }
            QMessageBox QPushButton:default:hover {
                background-color: #1e7e34;
            }
        """)
        
        if buttons:
            msg.setStandardButtons(buttons)
        if default_button:
            msg.setDefaultButton(default_button)
            
        return msg
    
    def show_info(self, title, text):
        """显示信息提示框"""
        msg = self.create_styled_message_box(QMessageBox.Icon.Information, title, text)
        return msg.exec()
    
    def show_warning(self, title, text):
        """显示警告提示框"""
        msg = self.create_styled_message_box(QMessageBox.Icon.Warning, title, text)
        return msg.exec()
    
    def show_error(self, title, text):
        """显示错误提示框"""
        msg = self.create_styled_message_box(QMessageBox.Icon.Critical, title, text)
        return msg.exec()
    
    def show_question(self, title, text, buttons=None, default_button=None):
        """显示问题对话框"""
        if buttons is None:
            buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        if default_button is None:
            default_button = QMessageBox.StandardButton.No
            
        msg = self.create_styled_message_box(QMessageBox.Icon.Question, title, text, buttons, default_button)
        return msg.exec()
    
    def reset_display_settings_to_default(self):
        """防呆功能：恢复默认显示设置"""
        reply = QMessageBox.question(
            self, 
            "恢复默认显示设置", 
            "🔧 这将恢复所有显示设置为默认值：\n\n"
            "• 字体颜色：黑色\n"
            "• 背景颜色：白色\n" 
            "• 字体类型：Microsoft YaHei\n"
            "• 字体大小：12px\n"
            "• 显示比例：100%\n"
            "• 其他字体样式：取消加粗/斜体/下划线\n"
            "• 跟随系统主题：启用\n\n"
            "💡 这可以解决文字看不见或显示异常的问题。\n\n"
            "是否确认恢复默认设置？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 恢复所有默认值
            self.settings.setValue("display_scale", 100)
            self.settings.setValue("font_color", "#000000")
            self.settings.setValue("background_color", "#ffffff")
            self.settings.setValue("font_family", "Microsoft YaHei")
            self.settings.setValue("font_size", 12)
            self.settings.setValue("font_bold", False)
            self.settings.setValue("font_italic", False)
            self.settings.setValue("font_underline", False)
            self.settings.setValue("use_system_theme", True)
            
            # 立即应用新设置
            self.display_scale = 100
            self.font_color = "#000000"
            self.background_color = "#ffffff" 
            self.font_family = "Microsoft YaHei"
            self.font_size = 12
            self.font_bold = False
            self.font_italic = False
            self.font_underline = False
            
            # 重新应用样式
            self.apply_consistent_styling()
            QTimer.singleShot(100, self.force_uniform_font_on_all_widgets)
            
            # 显示成功消息
            QMessageBox.information(
                self,
                "设置已恢复",
                "✅ 显示设置已成功恢复为默认值！\n\n"
                "🎯 所有文字现在应该清晰可见。\n"
                "💡 如果仍有显示问题，建议重启程序获得最佳效果。",
                QMessageBox.StandardButton.Ok
            )
            
            print("✅ 用户手动恢复了默认显示设置")
    
    def check_display_issues_on_startup(self):
        """启动时检查显示问题（防呆功能）"""
        try:
            # 检查字体颜色是否过浅
            hex_color = self.font_color.lstrip('#')
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                brightness = (r * 0.299 + g * 0.587 + b * 0.114) / 255
                
                # 如果亮度过高且背景也是白色，提示用户
                if brightness > 0.85 and self.background_color.lower() in ['#ffffff', '#fff', 'white']:
                    reply = QMessageBox.question(
                        self,
                        "显示问题提醒",
                        f"🔍 检测到可能的显示问题：\n\n"
                        f"当前字体颜色：{self.font_color} （亮度{brightness:.1%}）\n"
                        f"当前背景颜色：{self.background_color}\n\n"
                        f"⚠️ 浅色字体在白色背景上可能看不清楚，\n"
                        f"如果您遇到文字显示问题，建议恢复默认设置。\n\n"
                        f"💡 您可以通过菜单\"设置 → 恢复默认显示\"来解决。\n\n"
                        f"是否现在恢复默认显示设置？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.reset_display_settings_to_default()
                        
        except Exception as e:
            # 静默失败，不影响程序启动
            print(f"显示问题检查失败: {e}")
    
    def show_change_password(self):
        """显示修改密码对话框"""
        from auth_module.change_password_dialog import ChangePasswordDialog
        dialog = ChangePasswordDialog(self, self.username)
        dialog.exec()
    
    def show_invite_code_management(self):
        """显示邀请码管理对话框"""
        from auth_module.invite_code_dialog import InviteCodeDialog
        dialog = InviteCodeDialog(self)
        dialog.exec()
    
    def logout(self):
        """退出登录"""
        reply = QMessageBox.question(
            self, 
            "退出登录", 
            "确定要退出当前账号吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 停止心跳
            if self.heartbeat_timer:
                self.heartbeat_timer.stop()
            
            # 调用认证服务的登出方法
            if self.auth_service:
                self.auth_service.logout()
            
            # 关闭主窗口
            self.close()
            
            # 重启应用程序回到登录界面
            import subprocess
            subprocess.Popen([sys.executable] + sys.argv)
            QApplication.quit()
    
    def setup_status_bar(self):
        """设置状态栏"""
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage("伊利液奶奶科院 DHI筛查助手 - 准备就绪")
            status_bar.setStyleSheet(f"""
                QStatusBar {{
                    background-color: #e9ecef;
                    border-top: 1px solid #dee2e6;
                    padding: 8px 15px;
                }}
            """)
    
    def create_header(self):
        """创建顶部标题栏"""
        header = QWidget()
        
        # 根据屏幕高度设置标题栏高度
        screen_info = self.get_safe_screen_info()
        screen_height = screen_info['height']
        header_height = max(min(int(screen_height * 0.04), 50), 30)
        header.setFixedHeight(header_height)
        
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4285f4, stop:1 #1976d2);
                border: none;
            }
        """)
        
        layout = QHBoxLayout(header)
        # 减少上下边距，保持左右边距
        margin_h = max(int(header_height * 0.25), 15)
        margin_v = max(int(header_height * 0.15), 5)  # 减少垂直边距
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        # 左侧图标和标题
        title_layout = QHBoxLayout()
        
        # 图标
        icon_label = QLabel("🥛")
        icon_label.setStyleSheet(f"background: transparent;")
        title_layout.addWidget(icon_label)
        
        # 标题文字
        title_label = QLabel("DHI筛查助手")
        title_label.setStyleSheet(f"""
            font-weight: bold;
            color: white;
            background: transparent;
            margin-left: 10px;
        """)
        title_layout.addWidget(title_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # 用户信息区域
        user_layout = QHBoxLayout()
        user_layout.setSpacing(8)  # 适中的间距
        
        # 用户图标和名称
        user_icon = QLabel("👤")
        user_icon.setStyleSheet("background: transparent; color: white;")
        user_layout.addWidget(user_icon)
        
        # 获取用户姓名
        user_display = self.username
        if self.auth_service and hasattr(self.auth_service, 'get_user_name'):
            full_name = self.auth_service.get_user_name()
            if full_name and full_name != self.username:
                user_display = f"{self.username} ({full_name})"
        
        user_label = QLabel(f"当前用户: {user_display}")
        user_label.setStyleSheet("""
            color: white;
            background: transparent;
            font-weight: bold;
        """)
        user_layout.addWidget(user_label)
        
        # 注销按钮
        logout_btn = QPushButton("注销")
        logout_btn.setToolTip("退出登录")
        logout_btn.clicked.connect(self.logout)
        # 确保按钮有足够的宽度，降低高度
        logout_btn.setMinimumWidth(70)
        logout_btn.setMaximumHeight(26)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                color: white;
                padding: 3px 15px;
                font-weight: bold;
                font-size: 13px;
                min-width: 70px;
                max-height: 26px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        user_layout.addWidget(logout_btn)
        
        layout.addLayout(user_layout)
        
        # 快速设置按钮
        settings_btn = QPushButton("⚙️")
        settings_btn.setToolTip("显示设置")
        settings_btn.clicked.connect(self.show_display_settings)
        btn_size = max(int(header_height * 0.6), 20)
        settings_btn.setFixedSize(btn_size, btn_size)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: {btn_size // 2}px;
                color: white;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.3);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.4);
            }}
        """)
        layout.addWidget(settings_btn)
        
        # 右侧副标题
        subtitle_label = QLabel("伊利液奶奶科院 | DHI筛查助手")
        subtitle_label.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.8);
            background: transparent;
            margin-left: 10px;
        """)
        layout.addWidget(subtitle_label)
        
        return header
    
    def create_steps_indicator(self):
        """创建步骤指示器"""
        steps_widget = QWidget()
        
        # 根据屏幕大小设置步骤指示器高度
        screen_info = self.get_safe_screen_info()
        screen_width = screen_info['width']
        steps_height = max(min(int(screen_width * 0.05), 90), 70)
        steps_widget.setFixedHeight(steps_height)
        steps_widget.setStyleSheet("background-color: white; border-bottom: 1px solid #e0e0e0;")
        
        layout = QHBoxLayout(steps_widget)
        margin_h = max(int(screen_width * 0.03), 30)
        margin_v = max(int(steps_height * 0.2), 15)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        # 步骤数据
        steps = [
            {"number": "1", "title": "上传文件", "status": "completed"},
            {"number": "2", "title": "设置筛选条件", "status": "current"},
            {"number": "3", "title": "查看结果", "status": "pending"}
        ]
        
        for i, step in enumerate(steps):
            if i > 0:
                # 添加连接线
                line = QLabel()
                line.setFixedSize(80, 2)
                line.setStyleSheet("background-color: #e0e0e0; margin-top: 20px;")
                layout.addWidget(line)
            
            # 步骤圆圈和文字 - 水平布局
            step_layout = QHBoxLayout()
            step_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_layout.setSpacing(10)
            
            # 圆圈
            circle = QLabel(step["number"])
            # 获取DPI信息
            screen_info = self.get_safe_screen_info()
            dpi_ratio = screen_info['dpi_ratio']
            circle_size = max(int(24 * dpi_ratio * 0.6), 20)
            circle.setFixedSize(circle_size, circle_size)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            circle_font_size = max(int(12 * dpi_ratio * 0.6), 10)
            border_radius = circle_size // 2
            
            if step["status"] == "completed":
                circle.setStyleSheet(f"""
                    background-color: #28a745;
                    color: white;
                    border-radius: {border_radius}px;
                    font-weight: bold;
                    font-size: {circle_font_size}px;
                """)
            elif step["status"] == "current":
                circle.setStyleSheet(f"""
                    background-color: #007bff;
                    color: white;
                    border-radius: {border_radius}px;
                    font-weight: bold;
                    font-size: {circle_font_size}px;
                """)
            else:
                circle.setStyleSheet(f"""
                    background-color: #e0e0e0;
                    color: #666;
                    border-radius: {border_radius}px;
                    font-weight: bold;
                    font-size: {circle_font_size}px;
                """)
            
            step_layout.addWidget(circle)
            
            # 标题
            title = QLabel(step["title"])
            title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            step_title_font_size = max(int(13 * dpi_ratio * 0.7), 12)
            title.setStyleSheet(f"""
                font-size: {step_title_font_size}px;
                color: #333;
                margin-left: 5px;
            """)
            step_layout.addWidget(title)
            
            step_container = QWidget()
            step_container.setLayout(step_layout)
            layout.addWidget(step_container)
        
        layout.addStretch()
        return steps_widget
    
    def create_card_widget(self, title):
        """创建卡片样式的容器
        
        这是所有功能区域的统一容器组件，经过UI优化后采用紧凑设计：
        
        🎯 优化重点：
        1. 标题栏padding: 10px → 4px (减少60%)
        2. 标题栏margin: 10px → 4px (减少60%) 
        3. 标题字体: 16px → 13px (减少19%)
        4. 保持圆角和边框样式不变
        
        💡 设计理念：
        - 在保持美观的前提下最大化空间利用率
        - 所有卡片使用统一的紧凑样式
        - 确保文字仍然清晰可读
        """
        # 创建卡片主容器
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        # 设置卡片的大小策略 - 防止过度拉伸
        from PyQt6.QtWidgets import QSizePolicy
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        
        # 卡片主布局 - 零边距零间距，最大化内容空间
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 去除所有外边距
        main_layout.setSpacing(0)  # 去除所有间距
        
        # ===========================================
        # 🎯 标题栏优化 - 空间效率提升的关键
        # ===========================================
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 8px 8px 0 0;
                padding: 2px 4px;
            }
        """)  # ✅ 进一步压缩padding到2px 4px
        
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(2, 2, 2, 2)  # ✅ 进一步压缩margin到2px
        
        # 标题文字 - 字体优化
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #333;
            background: transparent;
        """)  # ✅ 字体从16px压缩到13px，保持加粗确保可读性
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addWidget(title_widget)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent; border: none;")
        main_layout.addWidget(content_widget)
        
        # 将内容区域的引用保存到卡片上，防止被垃圾回收
        setattr(card, 'content_widget', content_widget)
        
        return card
    
    def get_responsive_button_styles(self):
        """获取自适应按钮样式 - 使用统一字体大小"""
        # 使用统一的DPI缩放方法
        padding_v = self.get_dpi_scaled_size(8)
        padding_h = self.get_dpi_scaled_size(16)
        border_radius = self.get_dpi_scaled_size(5)
        min_height = self.get_dpi_scaled_size(32)  # 统一按钮最小高度
        
        return {
            'primary': f"""
                QPushButton {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: {border_radius}px;
                    padding: {padding_v}px {padding_h}px;
                    font-weight: bold;
                    min-height: {min_height}px;
                }}
                QPushButton:hover {{
                    background-color: #0056b3;
                }}
                QPushButton:pressed {{
                    background-color: #004085;
                }}
                QPushButton:disabled {{
                    background-color: #6c757d;
                    color: #adb5bd;
                }}
            """,
            'success': f"""
                QPushButton {{
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: {border_radius}px;
                    padding: {padding_v}px {padding_h}px;
                    font-weight: bold;
                    min-height: {min_height}px;
                }}
                QPushButton:hover {{
                    background-color: #218838;
                }}
                QPushButton:pressed {{
                    background-color: #1e7e34;
                }}
                QPushButton:disabled {{
                    background-color: #6c757d;
                    color: #adb5bd;
                }}
            """,
            'warning': f"""
                QPushButton {{
                    background-color: #ffc107;
                    color: #212529;
                    border: none;
                    border-radius: {border_radius}px;
                    padding: {padding_v}px {padding_h}px;
                    font-weight: bold;
                    min-height: {min_height}px;
                }}
                QPushButton:hover {{
                    background-color: #e0a800;
                }}
                QPushButton:pressed {{
                    background-color: #d39e00;
                }}
                QPushButton:disabled {{
                    background-color: #6c757d;
                    color: #adb5bd;
                }}
            """,
            'info': f"""
                QPushButton {{
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    border-radius: {border_radius}px;
                    padding: {padding_v}px {padding_h}px;
                    font-weight: bold;
                    min-height: {min_height}px;
                }}
                QPushButton:hover {{
                    background-color: #138496;
                }}
                QPushButton:pressed {{
                    background-color: #117a8b;
                }}
                QPushButton:disabled {{
                    background-color: #6c757d;
                    color: #adb5bd;
                }}
            """,
            'secondary': f"""
                QPushButton {{
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: {border_radius}px;
                    padding: {padding_v}px {padding_h}px;
                    font-weight: bold;
                    min-height: {min_height}px;
                }}
                QPushButton:hover {{
                    background-color: #5a6268;
                }}
                QPushButton:pressed {{
                    background-color: #545b62;
                }}
                QPushButton:disabled {{
                    background-color: #e9ecef;
                    color: #6c757d;
                }}
            """,
            'danger': f"""
                QPushButton {{
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: {border_radius}px;
                    padding: {padding_v}px {padding_h}px;
                    font-weight: bold;
                    min-height: {min_height}px;
                }}
                QPushButton:hover {{
                    background-color: #c82333;
                }}
                QPushButton:pressed {{
                    background-color: #bd2130;
                }}
                QPushButton:disabled {{
                    background-color: #e9ecef;
                    color: #6c757d;
                }}
            """
        }
    
    def get_responsive_form_styles(self):
        """获取自适应表单样式 - 使用统一字体大小"""
        # 使用统一的DPI缩放方法
        padding_v = self.get_dpi_scaled_size(6)  # 减少垂直内边距
        padding_h = self.get_dpi_scaled_size(12)  # 保持水平内边距
        border_radius = self.get_dpi_scaled_size(4)
        min_height = self.get_dpi_scaled_size(28)  # 统一输入框高度为28px
        
        return f"""
            QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                border: 2px solid #ced4da;
                border-radius: {border_radius}px;
                padding: {padding_v}px {padding_h}px;
                background-color: white;
                min-height: {min_height}px;
                color: #495057;
                selection-background-color: #007bff;
                selection-color: white;
            }}
            QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
                border-color: #007bff;
                outline: none;
                border-width: 2px;
            }}
            QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover {{
                border-color: #adb5bd;
            }}
            QLabel {{
                font-weight: 500;
                color: #495057;
                padding: 2px 0px;
            }}
            
            /* 确保下拉框和数字输入框的按钮显示正常 */
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {self.get_dpi_scaled_size(20)}px;
                border-left: 1px solid #ced4da;
                background-color: #f8f9fa;
                border-top-right-radius: {border_radius}px;
                border-bottom-right-radius: {border_radius}px;
            }}
            QComboBox::drop-down:hover {{
                background-color: #e9ecef;
            }}
            
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                width: {self.get_dpi_scaled_size(16)}px;
                min-height: {self.get_dpi_scaled_size(14)}px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover,
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: #e9ecef;
            }}
            
            QDateEdit::up-button, QDateEdit::down-button {{
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                width: {self.get_dpi_scaled_size(16)}px;
                min-height: {self.get_dpi_scaled_size(14)}px;
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {self.get_dpi_scaled_size(20)}px;
                border-left: 1px solid #ced4da;
                background-color: #f8f9fa;
                border-top-right-radius: {border_radius}px;
                border-bottom-right-radius: {border_radius}px;
            }}
        """
    
    def create_control_panel(self):
        """创建左侧控制面板 - 重构为4个功能标签页"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(panel)
        
        # 自适应边距和间距 - 使用优化的DPI适配
        margin = self.get_dpi_scaled_size(8)
        spacing = self.get_dpi_scaled_size(8)
        
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)

        # 创建功能标签页
        self.function_tabs = QTabWidget()
        
        # 自适应标签页样式 - 使用优化的DPI适配
        tab_font_size = self.get_dpi_scaled_font_size(16)  # 主标签页统一为16px
        tab_padding_v = self.get_dpi_scaled_size(12)
        tab_padding_h = self.get_dpi_scaled_size(20)
        tab_border_radius = self.get_dpi_scaled_size(5)
        
        self.function_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #e0e0e0;
                border-radius: {tab_border_radius}px;
                background-color: white;
                margin-top: -1px;
            }}
            QTabBar::tab {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: 2px;
                border-top-left-radius: {tab_border_radius}px;
                border-top-right-radius: {tab_border_radius}px;
                font-size: {tab_font_size}px;
                font-weight: 500;
                color: #495057;
                min-width: 120px;
                min-height: 35px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 1px solid white;
                color: #007bff;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: #e9ecef;
            }}
        """)
        
        # 创建4个功能标签页
        self.create_basic_data_tab()
        self.create_dhi_filter_tab()
        self.create_mastitis_screening_tab()
        
        # 隐性乳房炎月度监测标签页
        self.create_mastitis_monitoring_tab()
        
        layout.addWidget(self.function_tabs)
        
        return panel

    def create_basic_data_tab(self):
        """创建基础数据标签页：文件上传 + 在群牛文件 + 基础筛选条件
        
        这是主要的数据输入标签页，包含三个核心功能区域：
        1. 📁 文件上传 - DHI Excel文件选择和处理
        2. 🐄 在群牛文件 - 可选的在群牛数据文件
        3. 🔧 基础筛选条件 - 胎次和日期范围设置
        
        布局策略：采用顶部对齐设计，所有内容紧贴上方排列，下方留空
        这样用户打开标签页就能立即看到所有重要功能，无需滚动
        """
        # 创建标签页主容器
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # 设置布局参数 - 极度紧凑
        tab_layout.setSpacing(3)  # 组件间距：6px → 3px，进一步压缩
        tab_layout.setContentsMargins(4, 4, 4, 4)  # 外边距：8px → 4px，最小化空间浪费
        
        # 获取自适应样式 - 根据屏幕DPI自动调整
        button_styles = self.get_responsive_button_styles()  # 按钮样式字典
        form_styles = self.get_responsive_form_styles()      # 表单控件样式
        
        # 卡片内边距设置 - 平衡空间利用和内容可见性
        card_margin = self.get_dpi_scaled_size(8)  # 8px边距，既紧凑又不压缩内容
        
        # ===========================================
        # 1. 📁 DHI数据文件 - 超极简版本（无标题栏）
        # ===========================================
        # 直接创建容器，跳过create_card_widget以节省标题栏空间
        upload_group = QWidget()
        upload_group.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        # 设置文件上传区域的大小策略 - 防止过度拉伸
        from PyQt6.QtWidgets import QSizePolicy
        upload_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        upload_layout = QVBoxLayout(upload_group)
        upload_layout.setContentsMargins(4, 4, 4, 4)  # 进一步压缩边距
        upload_layout.setSpacing(1)  # 进一步压缩间距
        
        # 创建拖放上传区域 - 大幅增大高度
        drop_area = QWidget()
        drop_area.setFixedHeight(self.get_dpi_scaled_size(150))  # 增大高度为150px（约3倍），更易拖拽
        drop_area.setStyleSheet("""
            QWidget {
                border: 2px dashed #007bff;
                border-radius: 8px;
                background-color: #f8f9fa;
                margin: 2px;
            }
            QWidget:hover {
                background-color: #e9f4ff;
                border-color: #0056b3;
                border-width: 3px;
            }
        """)
        
        # 拖放区域布局 - 优化设计
        drop_layout = QHBoxLayout(drop_area)  # 改为水平布局，节省垂直空间
        drop_layout.setContentsMargins(20, 15, 20, 15)  # 进一步增大内边距
        drop_layout.setSpacing(15)  # 进一步增大间距
        
        # 上传图标
        upload_icon = QLabel("📤")
        upload_icon.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        drop_layout.addWidget(upload_icon)
        
        # 文字信息（垂直布局）
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        upload_text = QLabel("拖拽或点击选择DHI Excel文件")
        upload_text.setStyleSheet("font-size: 16px; color: #6c757d; background: transparent; border: none; font-weight: 500;")
        text_layout.addWidget(upload_text)
        
        format_hint = QLabel("支持 .xlsx, .xls 格式")
        format_hint.setStyleSheet("font-size: 13px; color: #9ca3af; background: transparent; border: none;")
        text_layout.addWidget(format_hint)
        
        drop_layout.addWidget(text_widget)
        drop_layout.addStretch()
        
        upload_layout.addWidget(drop_area)
        
        # 选择文件按钮（作为备选方式）
        self.upload_btn = QPushButton("📂 浏览文件")
        self.upload_btn.setStyleSheet(button_styles['secondary'])
        self.upload_btn.clicked.connect(self.select_files)
        # 移除最大高度限制，使用样式中的统一高度
        upload_layout.addWidget(self.upload_btn)
        
        # 已选文件显示区域 - 大幅增大高度（仅在有文件时显示）
        files_container = QWidget()
        self.files_layout = QVBoxLayout(files_container)
        self.files_layout.setContentsMargins(2, 2, 2, 2)  # 适当增加边距
        self.files_layout.setSpacing(2)  # 适当增加间距
        
        # 文件列表容器（用于动态添加文件标签）
        self.file_list = QListWidget()  # 保持兼容性
        self.file_list.setVisible(False)  # 隐藏传统列表
        
        # 文件标签容器
        self.file_tags_widget = QWidget()
        self.file_tags_layout = QVBoxLayout(self.file_tags_widget)
        self.file_tags_layout.setContentsMargins(4, 4, 4, 4)  # 进一步增加内边距
        self.file_tags_layout.setSpacing(6)  # 进一步增加间距
        
        no_files_label = QLabel("尚未选择文件")
        no_files_label.setStyleSheet("color: #9ca3af; font-size: 11px; font-style: italic;")
        self.file_tags_layout.addWidget(no_files_label)
        self.file_tags_layout.addStretch()
        
        # 用QScrollArea包裹文件标签区域，固定为12条数据的高度
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 计算12条数据的高度：每条36px + 间距6px = 42px，12条 = 504px
        single_file_height = self.get_dpi_scaled_size(36)  # 单个文件标签高度
        spacing = self.get_dpi_scaled_size(6)  # 间距
        total_height = (single_file_height + spacing) * 12  # 12条数据的总高度
        scroll_area.setFixedHeight(total_height)  # 固定高度，超出时显示滚动条
        
        scroll_area.setWidget(self.file_tags_widget)
        
        self.files_layout.addWidget(scroll_area)
        upload_layout.addWidget(files_container)
        
        # 操作按钮区域 - 极度压缩
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 1, 0, 0)  # 进一步压缩到1px
        buttons_layout.setSpacing(4)  # 进一步压缩到4px
        
        # 处理按钮
        self.process_btn = QPushButton("🚀 开始处理")
        self.process_btn.setStyleSheet(button_styles['primary'])
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        # 移除最大高度限制，使用样式中的统一高度
        buttons_layout.addWidget(self.process_btn)
        
        # 清空按钮
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setStyleSheet(button_styles['danger'])
        clear_btn.clicked.connect(self.clear_files)
        # 移除最大高度限制，使用样式中的统一高度
        buttons_layout.addWidget(clear_btn)
        
        buttons_layout.addStretch()
        upload_layout.addWidget(buttons_container)
        
        # 进度条 - 优化设计
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(self.get_dpi_scaled_size(6))  # 优化高度为6px
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #e9ecef;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        upload_layout.addWidget(self.progress_bar)
        
        # 进度标签（隐藏）
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        
        tab_layout.addWidget(upload_group)
        
        # 2. 在群牛文件上传区域 - 简洁设计，与主上传区域保持一致
        active_cattle_group = self.create_card_widget("🐄 在群牛文件")
        active_cattle_layout = QVBoxLayout(getattr(active_cattle_group, 'content_widget'))
        active_cattle_layout.setContentsMargins(0, 0, 0, 0)  # 移除双重边距
        active_cattle_layout.setSpacing(6)  # 与主上传区域保持一致的间距
        
        # 在群牛文件选择按钮
        self.active_cattle_btn = QPushButton("📋 选择在群牛文件")
        self.active_cattle_btn.setStyleSheet(button_styles['secondary'])
        self.active_cattle_btn.clicked.connect(self.select_active_cattle_file)
        # 移除最大高度限制，使用样式中的统一高度
        active_cattle_layout.addWidget(self.active_cattle_btn)
        
        # 在群牛文件状态标签 - 隐藏状态显示
        self.active_cattle_label = QLabel("")
        self.active_cattle_label.setVisible(False)  # 隐藏状态显示
        
        # 清除在群牛按钮
        self.clear_active_cattle_btn = QPushButton("🗑️ 清除在群牛")
        self.clear_active_cattle_btn.setStyleSheet(button_styles['danger'])
        self.clear_active_cattle_btn.clicked.connect(self.clear_active_cattle)
        self.clear_active_cattle_btn.setVisible(False)
        # 移除最大高度限制，使用样式中的统一高度
        active_cattle_layout.addWidget(self.clear_active_cattle_btn)
        
        tab_layout.addWidget(active_cattle_group)
        
        # 3. 基础筛选条件区域 - 简洁设计，统一边距策略
        basic_filter_group = self.create_card_widget("🔧 基础筛选条件")
        basic_filter_layout = QFormLayout(getattr(basic_filter_group, 'content_widget'))
        basic_filter_layout.setContentsMargins(0, 4, 0, 4)  # 只保留上下4px的细微边距
        basic_filter_layout.setVerticalSpacing(8)  # 适中的表单项间距
        basic_filter_layout.setHorizontalSpacing(10)
        basic_filter_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # 设置标签左对齐
        basic_filter_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # 设置表单左对齐
        
        # 胎次范围筛选
        parity_layout = QHBoxLayout()
        parity_layout.setSpacing(4)  # 减少间距
        self.parity_min = QSpinBox()
        self.parity_min.setRange(1, 99)
        self.parity_min.setValue(1)
        self.parity_min.setStyleSheet(form_styles)
        # 移除最大高度限制，使用样式中的统一高度
        
        self.parity_max = QSpinBox()
        self.parity_max.setRange(1, 99)
        self.parity_max.setValue(99)
        self.parity_max.setStyleSheet(form_styles)
        # 移除最大高度限制，使用样式中的统一高度
        
        parity_layout.addWidget(QLabel("从"))
        parity_layout.addWidget(self.parity_min)
        parity_layout.addWidget(QLabel("到"))
        parity_layout.addWidget(self.parity_max)
        parity_layout.addWidget(QLabel("胎"))
        parity_layout.addStretch()
        basic_filter_layout.addRow("胎次范围:", parity_layout)
        
        # 日期范围筛选
        date_layout = QHBoxLayout()
        date_layout.setSpacing(4)  # 减少间距
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addMonths(-12))  # 默认一年前
        self.date_start.setStyleSheet(form_styles)
        # 移除最大高度限制，使用样式中的统一高度
        
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())  # 默认今天
        self.date_end.setStyleSheet(form_styles)
        # 移除最大高度限制，使用样式中的统一高度
        
        date_layout.addWidget(self.date_start)
        date_layout.addWidget(QLabel("至"))
        date_layout.addWidget(self.date_end)
        date_layout.addStretch()
        basic_filter_layout.addRow("日期范围:", date_layout)
        
        tab_layout.addWidget(basic_filter_group)
        
        # ===========================================
        # 🎯 关键布局策略：顶部对齐设计
        # ===========================================
        # 这是界面优化的核心！addStretch()让所有内容紧贴上方排列
        # 
        # 效果说明：
        # - 文件上传、在群牛文件、基础筛选条件都集中在顶部
        # - 用户打开标签页立即看到所有重要功能，无需滚动
        # - 下方留空不影响使用，符合现代界面设计习惯
        # - 类似网页设计的顶部对齐布局
        #
        # 对比其他标签页：
        # - 基础数据、隐性乳房炎监测：使用 addStretch() 完全顶部对齐
        # - DHI筛选、慢性乳房炎：使用 addStretch(1) 适度分布
        tab_layout.addStretch()  # 🚀 顶部对齐的关键代码 - 内容集中上方，下方留空
        
        # 添加到标签页容器
        self.function_tabs.addTab(tab_widget, "📊 基础数据")

    def create_dhi_filter_tab(self):
        """创建DHI基础筛选标签页：蛋白筛选、体细胞数筛选、其他筛选项目、未来泌乳天数筛选"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # 获取自适应样式
        button_styles = self.get_responsive_button_styles()
        form_styles = self.get_responsive_form_styles()
        
        # 使用合理的边距，确保内容可见
        card_margin = self.get_dpi_scaled_size(10)
        
        # 1. 蛋白率筛选
        protein_group = self.create_special_filter_group("🥛 蛋白率筛选", "protein")
        tab_layout.addWidget(protein_group)
        
        # 2. 体细胞数筛选
        somatic_group = self.create_special_filter_group("🔬 体细胞数筛选", "somatic")
        tab_layout.addWidget(somatic_group)
        
        # 3. 其他筛选项目
        other_filters_group = self.create_card_widget("📋 其他筛选项目")
        other_filters_layout = QVBoxLayout(getattr(other_filters_group, 'content_widget'))
        other_filters_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 快捷选择按钮
        buttons_layout = QHBoxLayout()
        
        add_common_btn = QPushButton("➕ 快速添加常用项")
        add_common_btn.setStyleSheet(button_styles['info'])
        add_common_btn.clicked.connect(self.quick_add_common_filters)
        buttons_layout.addWidget(add_common_btn)
        
        select_all_btn = QPushButton("✅ 全选")
        select_all_btn.setStyleSheet(button_styles['secondary'])
        select_all_btn.clicked.connect(self.select_all_filters)
        buttons_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("❌ 全清")
        clear_all_btn.setStyleSheet(button_styles['secondary'])
        clear_all_btn.clicked.connect(self.clear_all_filters)
        buttons_layout.addWidget(clear_all_btn)
        
        buttons_layout.addStretch()
        other_filters_layout.addLayout(buttons_layout)
        
        # 创建多选界面
        multi_select_widget = QWidget()
        multi_select_layout = QVBoxLayout(multi_select_widget)
        
        # 标题和一键添加按钮
        header_layout = QHBoxLayout()
        select_label = QLabel("选择要添加的筛选项目（可多选）:")
        select_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 13px;")
        header_layout.addWidget(select_label)
        header_layout.addStretch()
        
        apply_btn = QPushButton("应用选中项目")
        apply_btn.setStyleSheet(button_styles['success'])
        apply_btn.clicked.connect(self.apply_selected_filters)
        header_layout.addWidget(apply_btn)
        
        multi_select_layout.addLayout(header_layout)
        
        # 筛选项目复选框网格
        self.filter_checkboxes = {}
        filters_grid = QGridLayout()
        
        # 从配置文件加载可选筛选项
        available_filters = {
            'fat_pct': '乳脂率(%)',
            'fat_protein_ratio': '脂蛋比',
            'somatic_cell_count': '体细胞数(万/ml)',
            'somatic_cell_score': '体细胞分',
            'urea_nitrogen': '尿素氮(mg/dl)',
            'lactose_pct': '乳糖率',
            'milk_loss': '奶损失(Kg)',
            'milk_payment_diff': '奶款差',
            'economic_loss': '经济损失',
            'corrected_milk': '校正奶(Kg)',
            'persistency': '持续力',
            'whi': 'WHI',
            'fore_milk_yield': '前奶量(Kg)',
            'fore_somatic_cell_count': '前体细胞(万/ml)',
            'fore_somatic_cell_score': '前体细胞分',
            'fore_milk_loss': '前奶损失(Kg)',
            'peak_milk_yield': '高峰奶(Kg)',
            'peak_days': '高峰日(天)',
            'milk_305': '305奶量(Kg)',
            'total_milk_yield': '总奶量(Kg)',
            'total_fat_pct': '总乳脂(%)',
            'total_protein_pct': '总蛋白(%)',
            'mature_equivalent': '成年当量(Kg)'
        }
        
        row = 0
        col = 0
        for filter_key, chinese_name in available_filters.items():
            checkbox = QCheckBox(chinese_name)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 12px;
                    color: #495057;
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 14px;
                    height: 14px;
                    border: 2px solid #ced4da;
                    border-radius: 3px;
                    background-color: white;
                }}
                QCheckBox::indicator:checked {{
                    background-color: #007bff;
                    border-color: #007bff;
                }}
            """)
            checkbox.toggled.connect(lambda checked, key=filter_key: self.on_filter_checkbox_toggled(key, checked))
            
            filters_grid.addWidget(checkbox, row, col)
            self.filter_checkboxes[filter_key] = checkbox
            
            col += 1
            if col >= 3:  # 每行3个
                col = 0
                row += 1
        
        multi_select_layout.addLayout(filters_grid)
        other_filters_layout.addWidget(multi_select_widget)
        
        # 已添加的筛选项容器
        added_label = QLabel("已添加的筛选项:")
        added_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 13px; margin-top: 10px;")
        other_filters_layout.addWidget(added_label)
        
        # 动态调整的筛选项容器（无滚动条）
        self.filters_container = QWidget()
        self.filters_container.setMinimumWidth(580)  # 进一步增加最小宽度
        self.filters_container.setMinimumHeight(200)  # 设置最小高度确保足够显示空间
        self.other_filters_layout = QVBoxLayout(self.filters_container)
        self.other_filters_layout.setContentsMargins(8, 8, 8, 8)
        self.other_filters_layout.setSpacing(8)  # 增加组件间距
        # 去掉addStretch，避免压缩筛选项
        
        # 直接添加容器，不使用滚动区域
        other_filters_layout.addWidget(self.filters_container)
        
        tab_layout.addWidget(other_filters_group)
        
        # 4. 未来泌乳天数筛选
        future_days_group = self.create_card_widget("📅 未来泌乳天数筛选")
        future_days_layout = QVBoxLayout(getattr(future_days_group, 'content_widget'))
        future_days_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 启用开关
        self.future_days_enabled = QCheckBox("启用未来泌乳天数筛选")
        self.future_days_enabled.setChecked(False)
        self.future_days_enabled.setStyleSheet(f"""
            QCheckBox {{
                font-size: 13px;
                color: #495057;
                spacing: 8px;
                font-weight: bold;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #ced4da;
                border-radius: 3px;
                background-color: white;
            }}
            QCheckBox::indicator:checked {{
                background-color: #28a745;
                border-color: #28a745;
            }}
        """)
        future_days_layout.addWidget(self.future_days_enabled)
        
        # 天数范围设置
        future_range_layout = QHBoxLayout()
        
        range_label = QLabel("未来泌乳天数范围:")
        range_label.setStyleSheet("color: #495057; font-weight: bold;")
        future_range_layout.addWidget(range_label)
        
        self.future_days_min = QSpinBox()
        self.future_days_min.setRange(1, 500)
        self.future_days_min.setValue(50)
        self.future_days_min.setStyleSheet(form_styles)
        future_range_layout.addWidget(self.future_days_min)
        
        dash_label4 = QLabel("—")
        dash_label4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_margin = self.get_dpi_scaled_size(8)
        dash_label4.setStyleSheet(f"color: #6c757d; margin: 0 {dash_margin}px;")
        future_range_layout.addWidget(dash_label4)
        
        self.future_days_max = QSpinBox()
        self.future_days_max.setRange(1, 500)
        self.future_days_max.setValue(350)
        self.future_days_max.setStyleSheet(form_styles)
        future_range_layout.addWidget(self.future_days_max)
        
        future_range_layout.addStretch()
        
        future_range_widget = QWidget()
        future_range_widget.setLayout(future_range_layout)
        future_days_layout.addWidget(future_range_widget)
        
        # 计划调群日期选择器
        plan_date_widget = QWidget()
        plan_date_layout = QHBoxLayout()
        plan_date_layout.setContentsMargins(0, 0, 0, 0)
        
        plan_date_label = QLabel("计划调群日期:")
        plan_date_label.setStyleSheet("font-weight: bold;")
        plan_date_layout.addWidget(plan_date_label)
        
        self.plan_date = QDateEdit()
        self.plan_date.setCalendarPopup(True)
        self.plan_date.setDate(QDate.currentDate().addDays(30))  # 默认30天后
        self.plan_date.setStyleSheet(form_styles)
        plan_date_layout.addWidget(self.plan_date)
        
        plan_date_layout.addStretch()
        plan_date_widget.setLayout(plan_date_layout)
        future_days_layout.addWidget(plan_date_widget)
        
        # 控制范围设置的启用状态
        def toggle_future_days_range():
            enabled = self.future_days_enabled.isChecked()
            self.future_days_min.setEnabled(enabled)
            self.future_days_max.setEnabled(enabled)
            self.plan_date.setEnabled(enabled)
            dash_label4.setEnabled(enabled)
            plan_date_label.setEnabled(enabled)
        
        self.future_days_enabled.toggled.connect(toggle_future_days_range)
        toggle_future_days_range()
        
        tab_layout.addWidget(future_days_group)
        
        # 5. 操作按钮
        action_group = self.create_card_widget("🚀 操作")
        action_layout = QVBoxLayout(getattr(action_group, 'content_widget'))
        action_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        action_spacing = self.get_dpi_scaled_size(10)
        action_layout.setSpacing(action_spacing)
        
        # 筛选按钮容器
        filter_buttons_layout = QHBoxLayout()
        
        # 筛选按钮
        self.filter_btn = QPushButton("🔍 开始筛选")
        self.filter_btn.setStyleSheet(button_styles['warning'])
        self.filter_btn.clicked.connect(self.start_filtering)
        self.filter_btn.setEnabled(False)
        filter_buttons_layout.addWidget(self.filter_btn)
        
        # 取消筛选按钮
        self.cancel_filter_btn = QPushButton("⏹️ 取消筛选")
        self.cancel_filter_btn.setStyleSheet(button_styles['danger'])
        self.cancel_filter_btn.clicked.connect(self.cancel_filtering)
        self.cancel_filter_btn.setEnabled(False)
        self.cancel_filter_btn.setVisible(False)
        filter_buttons_layout.addWidget(self.cancel_filter_btn)
        
        filter_buttons_widget = QWidget()
        filter_buttons_widget.setLayout(filter_buttons_layout)
        action_layout.addWidget(filter_buttons_widget)
        
        # 导出按钮
        self.export_btn = QPushButton("📥 导出Excel")
        self.export_btn.setStyleSheet(button_styles['info'])
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.export_btn)
        
        # 筛选进度
        self.filter_progress = QProgressBar()
        self.filter_progress.setVisible(False)
        
        progress_border_radius = self.get_dpi_scaled_size(4)
        progress_padding = self.get_dpi_scaled_size(2)
        progress_chunk_radius = self.get_dpi_scaled_size(3)
        min_height = self.get_dpi_scaled_size(20)
        
        self.filter_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #e0e0e0;
                border-radius: {progress_border_radius}px;
                text-align: center;
                padding: {progress_padding}px;
                background-color: #f8f9fa;
                min-height: {min_height}px;
            }}
            QProgressBar::chunk {{
                background-color: #ffc107;
                border-radius: {progress_chunk_radius}px;
            }}
        """)
        action_layout.addWidget(self.filter_progress)
        
        self.filter_label = QLabel("")
        self.filter_label.setStyleSheet(f"color: #495057; font-weight: 500;")
        action_layout.addWidget(self.filter_label)
        
        tab_layout.addWidget(action_group)
        
        # 添加适量弹性空间，保持布局平衡
        tab_layout.addStretch(1)  # 恢复少量弹性空间，避免内容过度压缩
        
        self.function_tabs.addTab(tab_widget, "🔬 DHI基础筛选")

    def load_filter_config(self, filter_key):
        """从配置文件加载筛选项目配置"""
        # 定义英文到中文的映射
        name_mapping = {
            'fat_pct': '乳脂率(%)',
            'fat_protein_ratio': '脂蛋比',
            'somatic_cell_count': '体细胞数(万/ml)',
            'somatic_cell_score': '体细胞分',
            'urea_nitrogen': '尿素氮(mg/dl)',
            'lactose_pct': '乳糖率',
            'milk_loss': '奶损失(Kg)',
            'milk_payment_diff': '奶款差',
            'economic_loss': '经济损失',
            'corrected_milk': '校正奶(Kg)',
            'persistency': '持续力',
            'whi': 'WHI',
            'fore_milk_yield': '前奶量(Kg)',
            'fore_somatic_cell_count': '前体细胞(万/ml)',
            'fore_somatic_cell_score': '前体细胞分',
            'fore_milk_loss': '前奶损失(Kg)',
            'peak_milk_yield': '高峰奶(Kg)',
            'peak_days': '高峰日(天)',
            'milk_305': '305奶量(Kg)',
            'total_milk_yield': '总奶量(Kg)',
            'total_fat_pct': '总乳脂(%)',
            'total_protein_pct': '总蛋白(%)',
            'mature_equivalent': '成年当量(Kg)'
        }
        
        try:
            import yaml
            with open('rules.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            optional_filters = config.get('optional_filters', {})
            if filter_key in optional_filters:
                filter_config = optional_filters[filter_key]
                # 如果配置中没有中文名称，使用映射表
                if 'chinese_name' not in filter_config:
                    filter_config['chinese_name'] = name_mapping.get(filter_key, filter_key)
                return filter_config
            else:
                # 返回默认配置，使用映射表中的中文名称
                return {
                    'chinese_name': name_mapping.get(filter_key, filter_key),
                    'min': 0.0,
                    'max': 100.0,
                    'min_match_months': 3,
                    'treat_empty_as_match': False
                }
        except Exception as e:
            print(f"加载筛选配置失败: {e}")
            # 出错时返回默认配置，使用映射表中的中文名称
            return {
                'chinese_name': name_mapping.get(filter_key, filter_key),
                'min': 0.0,
                'max': 100.0,
                'min_match_months': 3,
                'treat_empty_as_match': False
            }
    
    def on_system_type_changed(self, system_type: str):
        """系统类型改变时的处理函数"""
        try:
            print(f"系统类型已切换到: {system_type}")
            
            # 这里可以根据系统类型执行相应的逻辑
            # 例如：更新界面显示、重置某些设置等
            
            # 更新状态栏消息
            self.safe_show_status_message(f"已切换到{system_type}系统")
            
            # 如果需要，可以在这里添加更多的系统类型切换逻辑
            # 比如：
            # - 更新默认的筛选条件
            # - 重置某些界面元素
            # - 加载系统特定的配置
            
        except Exception as e:
            print(f"系统类型切换处理出错: {e}")
            # 不抛出异常，避免影响程序运行

    def create_mastitis_screening_tab(self):
        """创建牧场慢性乳房炎感染牛筛查处置标签页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # 获取自适应样式
        button_styles = self.get_responsive_button_styles()
        form_styles = self.get_responsive_form_styles()
        card_margin = self.get_dpi_scaled_size(12)
        
        # 1. 系统选择区域
        system_group = self.create_card_widget("🏥 选择数据管理系统")
        system_layout = QVBoxLayout(getattr(system_group, 'content_widget'))
        system_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 系统类型选择
        system_selection_layout = QHBoxLayout()
        
        self.mastitis_system_group = QWidget()
        system_radio_layout = QHBoxLayout(self.mastitis_system_group)
        system_radio_layout.setContentsMargins(0, 0, 0, 0)
        
        self.yiqiniu_radio = QCheckBox("伊起牛系统")
        self.yiqiniu_radio.setStyleSheet("color: black; background-color: white; font-weight: bold;")
        self.huimuyun_radio = QCheckBox("慧牧云系统")
        self.huimuyun_radio.setStyleSheet("color: black; background-color: white; font-weight: bold;")
        self.custom_radio = QCheckBox("其他系统")
        self.custom_radio.setStyleSheet("color: black; background-color: white; font-weight: bold;")
        
        # 设置为单选模式
        self.yiqiniu_radio.toggled.connect(lambda checked: self.on_mastitis_system_selected('yiqiniu', checked))
        self.huimuyun_radio.toggled.connect(lambda checked: self.on_mastitis_system_selected('huimuyun', checked))
        self.custom_radio.toggled.connect(lambda checked: self.on_mastitis_system_selected('custom', checked))
        
        system_radio_layout.addWidget(self.yiqiniu_radio)
        system_radio_layout.addWidget(self.huimuyun_radio)
        system_radio_layout.addWidget(self.custom_radio)
        system_radio_layout.addStretch()
        
        system_selection_layout.addWidget(self.mastitis_system_group)
        system_layout.addLayout(system_selection_layout)
        
        tab_layout.addWidget(system_group)
        
        # 2. 文件上传区域 - 动态显示
        self.mastitis_upload_group = self.create_card_widget("📁 上传相关数据文件")
        self.mastitis_upload_layout = QVBoxLayout(getattr(self.mastitis_upload_group, 'content_widget'))
        self.mastitis_upload_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 初始化文件上传控件
        self.mastitis_file_uploads = {}
        
        tab_layout.addWidget(self.mastitis_upload_group)
        self.mastitis_upload_group.setVisible(False)  # 默认隐藏
        
        # 3. 慢性感染牛识别配置
        chronic_group = self.create_card_widget("🔬 慢性感染牛识别标准")
        chronic_layout = QFormLayout(getattr(chronic_group, 'content_widget'))
        chronic_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        chronic_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # 设置标签左对齐
        chronic_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # 设置表单左对齐
        
        # 月份选择设置
        self.chronic_months_widget = QWidget()
        chronic_months_layout = QGridLayout(self.chronic_months_widget)
        chronic_months_layout.setContentsMargins(0, 0, 0, 0)
        
        # 初始化月份复选框字典
        self.chronic_month_checkboxes = {}
        
        # 默认显示提示信息
        no_data_label = QLabel("请先上传DHI数据以选择月份")
        no_data_label.setStyleSheet("color: #495057; font-style: italic; font-weight: 500;")
        chronic_months_layout.addWidget(no_data_label, 0, 0, 1, 3)
        
        chronic_months_label = QLabel("选择检查月份:")
        chronic_months_label.setStyleSheet("color: black; background-color: white; font-weight: bold;")
        chronic_layout.addRow(chronic_months_label, self.chronic_months_widget)
        
        # 体细胞数阈值设置
        scc_threshold_layout = QHBoxLayout()
        scc_threshold_combo = QComboBox()
        scc_threshold_combo.addItems(["<", "<=", "=", ">=", ">"])
        scc_threshold_combo.setCurrentText(">=")
        scc_threshold_combo.setStyleSheet(form_styles)
        scc_threshold_combo.setFixedWidth(70)
        
        self.scc_threshold_spin = QDoubleSpinBox()
        self.scc_threshold_spin.setRange(0.1, 100.0)
        self.scc_threshold_spin.setValue(20.0)
        self.scc_threshold_spin.setSuffix("万/ml")
        self.scc_threshold_spin.setDecimals(1)
        self.scc_threshold_spin.setStyleSheet(form_styles)
        
        scc_threshold_layout.addWidget(scc_threshold_combo)
        scc_threshold_layout.addWidget(self.scc_threshold_spin)
        scc_threshold_layout.addStretch()
        
        scc_threshold_widget = QWidget()
        scc_threshold_widget.setLayout(scc_threshold_layout)
        scc_label = QLabel("体细胞数:")
        scc_label.setStyleSheet("color: black; background-color: white; font-weight: bold;")
        chronic_layout.addRow(scc_label, scc_threshold_widget)
        
        # 存储阈值比较符号
        self.scc_threshold_combo = scc_threshold_combo
        
        tab_layout.addWidget(chronic_group)
        
        # 4. 处置办法配置
        treatment_group = self.create_card_widget("⚕️ 处置办法配置")
        treatment_layout = QVBoxLayout(getattr(treatment_group, 'content_widget'))
        treatment_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 创建5种处置办法的配置界面
        self.treatment_configs = {}
        
        treatment_methods = [
            ('cull', '淘汰', '🗑️'),
            ('isolate', '禁配隔离', '🚫'),
            ('blind_quarter', '瞎乳区', '👁️'),
            ('early_dry', '提前干奶', '⏰'),
            ('treatment', '治疗', '💊')
        ]
        
        for method_key, method_name, icon in treatment_methods:
            method_widget = self.create_treatment_config_widget(method_key, method_name, icon, form_styles)
            self.treatment_configs[method_key] = method_widget
            treatment_layout.addWidget(method_widget)
        
        tab_layout.addWidget(treatment_group)
        
        # 5. 操作按钮区域
        action_group = self.create_card_widget("🚀 执行筛查")
        action_layout = QVBoxLayout(getattr(action_group, 'content_widget'))
        action_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        buttons_layout = QHBoxLayout()
        
        self.mastitis_screen_btn = QPushButton("🔍 开始慢性乳房炎筛查")
        self.mastitis_screen_btn.setStyleSheet(button_styles['primary'])
        self.mastitis_screen_btn.clicked.connect(self.start_mastitis_screening)
        self.mastitis_screen_btn.setEnabled(False)
        buttons_layout.addWidget(self.mastitis_screen_btn)
        
        self.mastitis_export_btn = QPushButton("📤 导出筛查结果")
        self.mastitis_export_btn.setStyleSheet(button_styles['success'])
        self.mastitis_export_btn.clicked.connect(self.export_mastitis_results)
        self.mastitis_export_btn.setEnabled(False)
        buttons_layout.addWidget(self.mastitis_export_btn)
        
        buttons_layout.addStretch()
        action_layout.addLayout(buttons_layout)
        
        # 进度显示
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 5, 0, 5)
        
        # 进度条
        self.mastitis_progress = QProgressBar()
        self.mastitis_progress.setRange(0, 100)
        self.mastitis_progress.setValue(0)
        self.mastitis_progress.setVisible(False)
        self.mastitis_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                padding: 1px;
                background-color: #f0f0f0;
                height: 25px;
                font-size: 12px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.mastitis_progress)
        
        # 进度状态标签
        self.progress_status_label = QLabel("")
        self.progress_status_label.setStyleSheet("font-size: 12px; color: #495057; margin-top: 2px; font-weight: 500;")
        self.progress_status_label.setVisible(False)
        self.progress_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_status_label)
        
        action_layout.addWidget(progress_widget)
        
        self.mastitis_status_label = QLabel("请选择数据管理系统并上传相关文件")
        self.mastitis_status_label.setStyleSheet("color: #495057; font-size: 14px; padding: 10px; font-weight: 500;")
        action_layout.addWidget(self.mastitis_status_label)
        
        tab_layout.addWidget(action_group)
        
        # 添加适量弹性空间，保持布局平衡
        tab_layout.addStretch(1)  # 恢复少量弹性空间，避免内容过度压缩
        
        # 初始化变量
        self.current_mastitis_system = None
        self.mastitis_screening_results = None
        
        self.function_tabs.addTab(tab_widget, "🏥 慢性乳房炎筛查")

    def create_mastitis_monitoring_tab(self):
        """创建隐性乳房炎月度监测标签页"""
        try:
            import pyqtgraph as pg
        except ImportError:
            # 如果PyQtGraph未安装，显示错误信息
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            error_label = QLabel("缺少PyQtGraph依赖，请安装: pip install pyqtgraph")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #dc3545; padding: 20px;")
            tab_layout.addWidget(error_label)
            # 添加弹性空间，让内容紧贴上方
            tab_layout.addStretch()  # 内容集中在上方显示，下方留空
            self.function_tabs.addTab(tab_widget, "👁️ 隐性乳房炎监测")
            return

        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建标题
        title_label = QLabel("隐性乳房炎月度监测")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: black;
                background-color: white;
                padding: 10px 0px;
                border-bottom: 2px solid #3498db;
                margin-bottom: 15px;
            }
        """)
        tab_layout.addWidget(title_label)
        
        # 1. 顶部配置区域（简化为一行）
        config_card = self.create_card_widget("🛠️ 监测配置")
        config_layout = QHBoxLayout()
        config_layout.setSpacing(15)
        
        # 体细胞阈值设置
        threshold_label = QLabel("体细胞阈值:")
        threshold_label.setStyleSheet("font-weight: bold; color: black; background-color: white;")
        
        self.monitoring_scc_threshold = QDoubleSpinBox()
        self.monitoring_scc_threshold.setRange(1.0, 100.0)
        self.monitoring_scc_threshold.setValue(20.0)
        self.monitoring_scc_threshold.setSuffix(" 万/ml")
        self.monitoring_scc_threshold.setMaximumWidth(150)
        self.monitoring_scc_threshold.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                color: black;
                background-color: white;
                font-weight: bold;
            }
            QDoubleSpinBox:focus {
                border-color: #3498db;
                color: black;
            }
        """)
        
        # 按钮组
        button_styles = self.get_responsive_button_styles()
        
        self.start_monitoring_btn = QPushButton("🔍 开始分析")
        self.start_monitoring_btn.setStyleSheet(button_styles['primary'])
        self.start_monitoring_btn.clicked.connect(self.start_mastitis_monitoring)
        self.start_monitoring_btn.setMaximumWidth(120)
        
        self.export_monitoring_btn = QPushButton("📤 导出Excel")
        self.export_monitoring_btn.setStyleSheet(button_styles['success'])
        self.export_monitoring_btn.clicked.connect(self.export_monitoring_results)
        self.export_monitoring_btn.setEnabled(False)
        self.export_monitoring_btn.setMaximumWidth(120)
        
        # 状态显示
        self.monitoring_status_label = QLabel("请先上传牛群基础信息，然后上传DHI数据进行分析")
        self.monitoring_status_label.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 12px;
                padding: 8px 12px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border-left: 4px solid #ffc107;
                font-weight: bold;
            }
        """)
        

        
        # 数据状态显示
        self.monitoring_data_status = QLabel()
        self.monitoring_data_status.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 11px;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border-left: 4px solid #17a2b8;
                font-weight: bold;
            }
        """)
        self.update_monitoring_data_status()
        
        # 添加到配置布局
        config_layout.addWidget(threshold_label)
        config_layout.addWidget(self.monitoring_scc_threshold)
        config_layout.addWidget(self.start_monitoring_btn)
        config_layout.addWidget(self.export_monitoring_btn)
        config_layout.addStretch()
        
        config_card.layout().addLayout(config_layout)
        config_card.layout().addWidget(self.monitoring_data_status)
        config_card.layout().addWidget(self.monitoring_status_label)
        tab_layout.addWidget(config_card)
        
        # 添加弹性空间，让内容紧贴上方
        tab_layout.addStretch()  # 内容集中在上方显示，下方留空
        
        # 初始化监测计算器
        self.mastitis_monitoring_calculator = None
        self.mastitis_monitoring_results = None
        
        self.function_tabs.addTab(tab_widget, "👁️ 隐性乳房炎监测")
        
        # 创建尿素氮追踪标签页
        self.create_urea_tracking_tab()
    
    def create_urea_tracking_tab(self):
        """创建尿素氮追踪标签页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(20, 20, 20, 20)
        tab_layout.setSpacing(15)
        
        # 功能说明按钮
        help_btn = QPushButton("❓ 说明")
        help_btn.setObjectName("helpButton")
        help_btn.clicked.connect(self.show_urea_tracking_help)
        help_btn.setMaximumWidth(120)
        # 强制设置按钮样式，确保文字是黑色
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: black;
                border: 1px solid #dee2e6;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        tab_layout.addWidget(help_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        # 移除启用开关，因为不需要
        
        # 分析设置组
        analysis_group = QGroupBox("分析设置")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.urea_arithmetic_radio = QRadioButton("算术平均值")
        self.urea_weighted_radio = QRadioButton("加权平均值")
        self.urea_both_radio = QRadioButton("同时显示两者（默认）")
        self.urea_both_radio.setChecked(True)
        
        analysis_layout.addWidget(self.urea_arithmetic_radio)
        analysis_layout.addWidget(self.urea_weighted_radio)
        analysis_layout.addWidget(self.urea_both_radio)
        
        tab_layout.addWidget(analysis_group)
        
        # 数据筛选组
        filter_group = QGroupBox("数据筛选")
        filter_layout = QGridLayout(filter_group)
        
        self.urea_filter_outliers = QCheckBox("筛选异常值")
        self.urea_filter_outliers.toggled.connect(self.on_urea_filter_toggled)
        filter_layout.addWidget(self.urea_filter_outliers, 0, 0, 1, 2)
        
        filter_layout.addWidget(QLabel("尿素氮范围："), 1, 0, 1, 2)
        
        filter_layout.addWidget(QLabel("最小值："), 2, 0)
        self.urea_min_value = QSpinBox()
        self.urea_min_value.setRange(0, 50)
        self.urea_min_value.setValue(5)
        self.urea_min_value.setSuffix(" mg/dl")
        self.urea_min_value.setEnabled(False)
        filter_layout.addWidget(self.urea_min_value, 2, 1)
        
        filter_layout.addWidget(QLabel("最大值："), 3, 0)
        self.urea_max_value = QSpinBox()
        self.urea_max_value.setRange(0, 100)
        self.urea_max_value.setValue(30)
        self.urea_max_value.setSuffix(" mg/dl")
        self.urea_max_value.setEnabled(False)
        filter_layout.addWidget(self.urea_max_value, 3, 1)
        
        tab_layout.addWidget(filter_group)
        
        # 泌乳天数分组
        lactation_group = QGroupBox("泌乳天数分组")
        lactation_layout = QVBoxLayout(lactation_group)
        
        # 创建分组复选框
        self.urea_lactation_groups = {}
        groups = [
            "1-30天", "31-60天", "61-90天", "91-120天",
            "121-150天", "151-180天", "181-210天", "211-240天",
            "241-270天", "271-300天", "301-330天", "331天以上"
        ]
        
        # 使用网格布局显示分组
        groups_widget = QWidget()
        groups_grid = QGridLayout(groups_widget)
        groups_grid.setSpacing(10)
        
        for i, group in enumerate(groups):
            checkbox = QCheckBox(group)
            checkbox.setChecked(True)  # 默认全选
            self.urea_lactation_groups[group] = checkbox
            groups_grid.addWidget(checkbox, i // 3, i % 3)
        
        lactation_layout.addWidget(groups_widget)
        
        # 全选/清除按钮
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(lambda: self.toggle_urea_groups(True))
        clear_all_btn = QPushButton("清除")
        clear_all_btn.clicked.connect(lambda: self.toggle_urea_groups(False))
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(clear_all_btn)
        btn_layout.addStretch()
        lactation_layout.addLayout(btn_layout)
        
        tab_layout.addWidget(lactation_group)
        
        # 最少样本数设置
        sample_layout = QHBoxLayout()
        sample_layout.addWidget(QLabel("最少样本数："))
        self.urea_min_sample = QSpinBox()
        self.urea_min_sample.setRange(1, 50)
        self.urea_min_sample.setValue(5)
        self.urea_min_sample.setSuffix("头")
        sample_layout.addWidget(self.urea_min_sample)
        sample_layout.addWidget(QLabel("（少于此数量的组不显示）"))
        sample_layout.addStretch()
        tab_layout.addLayout(sample_layout)
        
        # 分析按钮
        btn_layout = QHBoxLayout()
        
        # 开始分析按钮
        self.urea_analyze_btn = QPushButton("开始分析")
        self.urea_analyze_btn.setEnabled(False)  # 默认禁用，直到有数据
        self.urea_analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.urea_analyze_btn.clicked.connect(self.perform_urea_tracking_analysis)
        btn_layout.addWidget(self.urea_analyze_btn)
        
        # 导出Excel按钮  
        self.urea_export_btn = QPushButton("导出Excel")
        self.urea_export_btn.setEnabled(False)  # 默认禁用，直到有结果
        self.urea_export_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.urea_export_btn.clicked.connect(self.export_urea_tracking_results)
        btn_layout.addWidget(self.urea_export_btn)
        
        btn_layout.addStretch()
        tab_layout.addLayout(btn_layout)
        
        # 添加弹性空间
        tab_layout.addStretch()
        
        self.function_tabs.addTab(tab_widget, "🧪 尿素氮追踪")
    
    def show_urea_tracking_help(self):
        """显示尿素氮追踪功能说明"""
        help_text = """
        <h2>尿素氮追踪分析说明</h2>
        
        <h3>功能概述</h3>
        <p>本功能通过追踪不同泌乳阶段牛群的尿素氮水平变化，帮助您优化日粮配方和蛋白质利用效率。</p>
        
        <h3>分析逻辑</h3>
        <ol>
            <li><b>分组依据</b>：基于最新一次DHI数据中每头牛的泌乳天数进行分组<br>
                例如：2024年4月数据中，泌乳天数75天的牛被分到"2024年4月 61-90天"组</li>
            <li><b>历史追踪</b>：
                <ul>
                    <li>确定当前组内的牛只（如50头）</li>
                    <li>在历史DHI数据中查找这些牛的尿素氮记录</li>
                    <li>如某月只有30头有数据，则计算这30头的平均值</li>
                </ul>
            </li>
            <li><b>计算方法</b>：
                <ul>
                    <li>算术平均：所有牛只尿素氮值的简单平均</li>
                    <li>加权平均：考虑产奶量的加权平均<br>
                        公式：Σ(尿素氮×产奶量) / Σ(产奶量)</li>
                </ul>
            </li>
        </ol>
        
        <h3>使用说明</h3>
        <ol>
            <li>确保已在"基础数据"中上传多个月份的DHI数据</li>
            <li>选择要分析的泌乳天数组</li>
            <li>设置异常值筛选范围（可选）</li>
            <li>点击主界面的"开始筛选"按钮</li>
            <li>在"筛选结果-尿素氮追踪"查看结果</li>
        </ol>
        
        <h3>结果解读</h3>
        <ul>
            <li><b>上升趋势</b>：可能表示日粮蛋白过量或瘤胃能量不足</li>
            <li><b>下降趋势</b>：日粮调整有效，蛋白利用率提高</li>
            <li><b>正常范围</b>：一般为12-18 mg/dl</li>
        </ul>
        
        <h3>注意事项</h3>
        <ul>
            <li>分组基于最新数据，历史数据仅用于趋势分析</li>
            <li>样本数过少的组可能导致数据波动较大</li>
        </ul>
        """
        
        dialog = QDialog(self)
        dialog.setWindowTitle("尿素氮追踪功能说明")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # 使用 QTextEdit 显示 HTML
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(help_text)
        layout.addWidget(text_edit)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()
    
    def on_urea_filter_toggled(self, checked):
        """切换异常值筛选时启用/禁用输入框"""
        self.urea_min_value.setEnabled(checked)
        self.urea_max_value.setEnabled(checked)
    
    def toggle_urea_groups(self, select_all):
        """全选或清除尿素氮分组"""
        for checkbox in self.urea_lactation_groups.values():
            checkbox.setChecked(select_all)
    
    def perform_urea_tracking_analysis(self):
        """执行尿素氮追踪分析"""
        # 移除启用检查，直接进行分析
        
        if not self.urea_tracker.dhi_data_dict:
            QMessageBox.warning(self, "警告", "没有可用的DHI数据，请先上传DHI文件")
            return
        
        # 收集选中的泌乳天数组
        selected_groups = []
        for group_name, checkbox in self.urea_lactation_groups.items():
            if checkbox.isChecked():
                selected_groups.append(group_name)
        
        if not selected_groups:
            QMessageBox.warning(self, "警告", "请至少选择一个泌乳天数组")
            return
        
        # 获取显示模式
        if self.urea_arithmetic_radio.isChecked():
            value_type = 'arithmetic'
        elif self.urea_weighted_radio.isChecked():
            value_type = 'weighted'
        else:
            value_type = 'both'
        
        try:
            # 定义异步分析任务
            def analyze_task(progress_callback=None, status_callback=None, check_cancelled=None):
                if status_callback:
                    status_callback("正在准备分析...")
                
                # 执行分析
                results = self.urea_tracker.analyze(
                    selected_groups=selected_groups,
                    filter_outliers=self.urea_filter_outliers.isChecked(),
                    min_value=self.urea_min_value.value() if self.urea_filter_outliers.isChecked() else 5.0,
                    max_value=self.urea_max_value.value() if self.urea_filter_outliers.isChecked() else 30.0,
                    min_sample_size=self.urea_min_sample.value()
                )
                
                if progress_callback:
                    progress_callback(100)
                    
                return results
            
            # 使用异步进度管理器执行分析
            progress_manager = AsyncProgressManager(self)
            results = progress_manager.execute_with_progress(
                analyze_task,
                title="尿素氮追踪分析",
                cancel_text="取消",
                total_steps=100
            )
            
            if 'error' in results:
                QMessageBox.warning(self, "警告", results['error'])
                return
            
            if not results:
                QMessageBox.information(self, "提示", "没有符合条件的数据")
                return
            
            # 保存结果
            self.urea_tracking_results = {
                'results': results,
                'value_type': value_type
            }
            
            # 在结果标签页中添加尿素氮追踪标签
            self.add_urea_tracking_tab()
            
            # 启用导出按钮
            self.urea_export_btn.setEnabled(True)
            
            # 显示成功消息
            group_count = len(results)
            total_history_points = sum(len(group['history']) for group in results.values())
            QMessageBox.information(
                self, 
                "分析完成", 
                f"尿素氮追踪分析完成！\n\n"
                f"分析了 {group_count} 个泌乳天数组\n"
                f"共 {total_history_points} 个历史数据点\n\n"
                f"请查看右侧'筛选结果'中的'尿素氮追踪'标签页"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败: {str(e)}")
    
    def create_urea_tracking_result_tab(self):
        """创建尿素氮追踪结果标签页（初始为空）"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # 创建一个占位标签
        placeholder = QLabel("尿素氮追踪分析结果将在这里显示\n\n请先上传DHI数据，然后在左侧'尿素氮追踪'标签页中点击'开始分析'")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 50px;
            }
        """)
        tab_layout.addWidget(placeholder)
        
        # 保存占位符引用，以便后续替换
        self.urea_placeholder = placeholder
        self.urea_result_tab_widget = tab_widget
        self.urea_result_tab_layout = tab_layout
        
        self.result_sub_tabs.addTab(tab_widget, "🧪 尿素氮追踪")
    
    def add_urea_tracking_tab(self):
        """更新尿素氮追踪结果标签页的内容"""
        if not self.urea_tracking_results or not hasattr(self, 'urea_result_tab_layout'):
            return
        
        # 清空现有内容
        while self.urea_result_tab_layout.count():
            child = self.urea_result_tab_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上部分：图表显示
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        # 图表标题
        chart_title = QLabel("尿素氮历史趋势图")
        chart_title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        chart_layout.addWidget(chart_title)
        
        # 创建pyqtgraph图表
        try:
            import pyqtgraph as pg
            
            # 创建图表控件（使用中文化的图表部件）
            if ChinesePlotWidget:
                self.urea_chart = ChinesePlotWidget()
            else:
                self.urea_chart = pg.PlotWidget()
            
            self.urea_chart.setLabel('left', '尿素氮 (mg/dl)', color='black')
            self.urea_chart.setLabel('bottom', '月份', color='black')
            self.urea_chart.showGrid(x=True, y=True, alpha=0.3)
            self.urea_chart.setMinimumHeight(250)
            
            # 设置图表背景色和轴颜色
            self.urea_chart.setBackground('white')
            axis_pen = pg.mkPen(color='black', width=1)
            self.urea_chart.getAxis('left').setPen(axis_pen)
            self.urea_chart.getAxis('left').setTextPen('black')
            self.urea_chart.getAxis('bottom').setPen(axis_pen)
            self.urea_chart.getAxis('bottom').setTextPen('black')
            
            # 设置图例样式
            legend = self.urea_chart.addLegend()
            legend.setBrush(pg.mkBrush(255, 255, 255, 200))  # 白色半透明背景
            legend.setPen(pg.mkPen(0, 0, 0))  # 黑色边框
            
            # 绘制数据
            self.plot_urea_tracking_data()
            
            chart_layout.addWidget(self.urea_chart)
        except ImportError:
            # 如果没有安装pyqtgraph，显示提示信息
            chart_placeholder = QTextEdit()
            chart_placeholder.setReadOnly(True)
            chart_placeholder.setPlainText("图表功能需要安装pyqtgraph库\n\n请运行: pip install pyqtgraph")
            chart_layout.addWidget(chart_placeholder)
        
        splitter.addWidget(chart_widget)
        
        # 下部分：数据表格
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # 表格标题
        table_title = QLabel("尿素氮分析数据表")
        table_title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        table_layout.addWidget(table_title)
        
        # 创建数据表格
        data_table = QTableWidget()
        
        # 设置表格响应式特性
        data_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        data_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        data_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 从结果中构建表格数据
        results = self.urea_tracking_results['results']
        value_type = self.urea_tracking_results['value_type']
        
        # 获取汇总DataFrame
        summary_df = self.urea_tracker.get_summary_dataframe(results)
        
        if not summary_df.empty:
            # 设置表格
            data_table.setRowCount(len(summary_df))
            data_table.setColumnCount(len(summary_df.columns))
            data_table.setHorizontalHeaderLabels(summary_df.columns.tolist())
            
            # 填充数据
            for row_idx in range(len(summary_df)):
                for col_idx in range(len(summary_df.columns)):
                    value = summary_df.iloc[row_idx, col_idx]
                    item = QTableWidgetItem(str(value))
                    data_table.setItem(row_idx, col_idx, item)
            
            # 设置列宽调整模式
            header = data_table.horizontalHeader()
            # 设置前几列为固定宽度
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 泌乳天数组
            # 其他列自动拉伸
            for i in range(1, data_table.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            
            # 设置最后一列拉伸填充剩余空间
            header.setStretchLastSection(True)
            
            # 初始调整列宽
            data_table.resizeColumnsToContents()
            
            # 设置最小列宽
            for i in range(data_table.columnCount()):
                if data_table.columnWidth(i) < 80:
                    data_table.setColumnWidth(i, 80)
        
        table_layout.addWidget(data_table)
        
        splitter.addWidget(table_widget)
        
        # 设置分割比例
        splitter.setSizes([300, 400])
        
        self.urea_result_tab_layout.addWidget(splitter)
        
        # 切换到尿素氮追踪标签页
        for i in range(self.result_sub_tabs.count()):
            if self.result_sub_tabs.tabText(i) == "🧪 尿素氮追踪":
                self.result_sub_tabs.setCurrentIndex(i)
                break
        
        # 同时切换主标签页到筛选结果
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "📊 筛选结果":
                self.tab_widget.setCurrentIndex(i)
                break
    
    def plot_urea_tracking_data(self):
        """绘制尿素氮追踪数据图表"""
        if not self.urea_tracking_results or not hasattr(self, 'urea_chart'):
            return
        
        try:
            import pyqtgraph as pg
            
            # 清空现有图表
            self.urea_chart.clear()
            
            # 获取数据
            results = self.urea_tracking_results['results']
            value_type = self.urea_tracking_results['value_type']
            
            # 获取图表数据
            chart_data = self.urea_tracker.get_chart_data(results, value_type)
            
            if not chart_data['dates']:
                return
            
            # 准备X轴数据（月份索引）
            x_values = list(range(len(chart_data['dates'])))
            
            # 颜色列表
            colors = [
                (255, 0, 0),      # 红色
                (0, 255, 0),      # 绿色
                (0, 0, 255),      # 蓝色
                (255, 255, 0),    # 黄色
                (255, 0, 255),    # 品红
                (0, 255, 255),    # 青色
                (255, 128, 0),    # 橙色
                (128, 0, 255),    # 紫色
                (0, 128, 255),    # 天蓝
                (255, 0, 128),    # 玫红
                (128, 255, 0),    # 黄绿
                (128, 128, 255),  # 淡紫
            ]
            
            # 绘制每个系列的数据
            for i, series in enumerate(chart_data['series']):
                # 过滤掉None值
                valid_points = []
                valid_x = []
                for j, value in enumerate(series['data']):
                    if value is not None:
                        valid_points.append(value)
                        valid_x.append(x_values[j])
                
                if valid_points:
                    color = colors[i % len(colors)]
                    pen = pg.mkPen(color=color, width=2)
                    
                    # 绘制线条
                    self.urea_chart.plot(
                        valid_x, valid_points,
                        pen=pen,
                        symbol='o',
                        symbolSize=8,
                        symbolBrush=color,
                        name=series['name']
                    )
            
            # 设置X轴标签
            x_axis = self.urea_chart.getAxis('bottom')
            x_axis.setTicks([[(i, date) for i, date in enumerate(chart_data['dates'])]])
            
            # 设置Y轴范围
            self.urea_chart.setYRange(0, 35)  # 尿素氮的合理范围
            
        except Exception as e:
            logger.error(f"绘制尿素氮图表失败: {e}")
            print(f"绘制尿素氮图表失败: {e}")
    
    def export_urea_tracking_results(self):
        """导出尿素氮追踪结果到Excel"""
        if not self.urea_tracking_results:
            QMessageBox.warning(self, "警告", "没有可导出的尿素氮追踪结果")
            return
        
        try:
            # 选择保存文件
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "保存尿素氮追踪结果",
                f"尿素氮追踪分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel文件 (*.xlsx)"
            )
            
            if not filename:
                return
            
            # 创建Excel写入器
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 1. 汇总表
                results = self.urea_tracking_results['results']
                summary_df = self.urea_tracker.get_summary_dataframe(results)
                if not summary_df.empty:
                    summary_df.to_excel(writer, sheet_name='汇总数据', index=False)
                
                # 2. 详细牛只清单
                detail_df = self.urea_tracker.get_detail_dataframe(results)
                if not detail_df.empty:
                    detail_df.to_excel(writer, sheet_name='详细牛只清单', index=False)
                
                # 3. 分析说明
                info_data = {
                    '项目': ['分析时间', '最新数据月份', '分析组数', '总记录数'],
                    '值': [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        self.urea_tracker.latest_date or '无',
                        len(results),
                        len(detail_df) if not detail_df.empty else 0
                    ]
                }
                info_df = pd.DataFrame(info_data)
                info_df.to_excel(writer, sheet_name='分析信息', index=False)
            
            QMessageBox.information(self, "成功", f"尿素氮追踪结果已导出到:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def update_monitoring_data_status(self):
        """更新隐性乳房炎监测的数据状态显示 - 取消所有状态显示"""
        # 清空状态显示
        self.monitoring_data_status.setText("")
    
    def get_mastitis_monitoring_formula_html(self):
        """获取隐性乳房炎监测公式说明HTML"""
        return """
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">📊 隐性乳房炎月度监测指标计算公式</h3>
            
            <h4 style="color: #e67e22;">1. 当月流行率 (%)</h4>
            <p><strong>公式:</strong> 体细胞数(万/ml) > 阈值的牛头数 ÷ 当月参测牛头数 × 100</p>
            <p><strong>数据来源:</strong> DHI报告 - 体细胞计数字段</p>
            
            <h4 style="color: #e67e22;">2. 新发感染率 (%)</h4>
            <p><strong>公式:</strong> (当月SCC>阈值 且 上月SCC≤阈值的牛头数) ÷ (上月SCC≤阈值的牛头数) × 100</p>
            <p><strong>数据来源:</strong> 连续两个月DHI报告对比</p>
            <p><strong>注意:</strong> 需要至少2个月的数据，基于管理号匹配重叠牛只</p>
            
            <h4 style="color: #e67e22;">3. 慢性感染率 (%)</h4>
            <p><strong>公式:</strong> (当月SCC>阈值 且 上月SCC>阈值的牛头数) ÷ (上月SCC>阈值的牛头数) × 100</p>
            <p><strong>数据来源:</strong> 连续两个月DHI报告对比</p>
            
            <h4 style="color: #e67e22;">4. 慢性感染牛占比 (%)</h4>
            <p><strong>公式:</strong> (当月SCC>阈值 且 上月SCC>阈值的牛头数) ÷ (当月参测牛头数) × 100</p>
            <p><strong>数据来源:</strong> 连续两个月DHI报告对比</p>
            
            <h4 style="color: #e67e22;">5. 头胎/经产首测流行率 (%)</h4>
            <p><strong>公式:</strong> (胎次=1/胎次>1 且 DIM5-35天 且 SCC>阈值的牛头数) ÷ (相应胎次且DIM5-35天的参测牛头数) × 100</p>
            <p><strong>数据来源:</strong> DHI报告 - 胎次、泌乳天数、体细胞计数字段</p>
            
            <h4 style="color: #e67e22;">6. 干奶前流行率 (%)</h4>
            <p><strong>公式:</strong> (在胎天数>180天 且 SCC>阈值的牛头数) ÷ (在胎天数>180天的参测牛头数) × 100</p>
            <p><strong>数据来源:</strong> DHI报告 + 牛群基础信息 (管理号与耳号匹配)</p>
            <p><strong>数据要求:</strong></p>
            <ul>
                <li>必须先在"慢性乳房炎筛查"中上传牛群基础信息</li>
                <li>牛群基础信息需包含耳号和在胎天数字段</li>
                <li>DHI数据的管理号需要能与牛群基础信息的耳号匹配</li>
                <li>系统会自动去除前导0进行匹配</li>
            </ul>
            <p><strong>常见问题:</strong></p>
            <ul>
                <li>如果显示"数据无法匹配"，通常是DHI数据与牛群信息来自不同时间点</li>
                <li>如果显示"无在胎天数数据"，说明匹配的牛只当时处于空怀状态</li>
                <li>如果显示"无符合条件牛只"，说明当前没有在胎天数>180天的牛</li>
            </ul>
            <p><strong>数据要求:</strong></p>
            <ul>
                <li>必须先在"慢性乳房炎筛查"中上传牛群基础信息</li>
                <li>牛群基础信息需包含耳号和在胎天数字段</li>
                <li>DHI数据的管理号需要能与牛群基础信息的耳号匹配</li>
                <li>系统会自动去除前导0进行匹配</li>
            </ul>
            <p><strong>常见问题:</strong></p>
            <ul>
                <li>如果显示"数据无法匹配"，通常是DHI数据与牛群信息来自不同时间点</li>
                <li>如果显示"无在胎天数数据"，说明匹配的牛只当时处于空怀状态</li>
                <li>如果显示"无符合条件牛只"，说明当前没有在胎天数>180天的牛</li>
            </ul>
            
            <h4 style="color: #27ae60;">⚠️ 重要说明</h4>
            <ul>
                <li><strong>体细胞阈值:</strong> 默认20万/ml，可在界面上方调整</li>
                <li><strong>数据匹配:</strong> 基于管理号标准化匹配，自动去除前导0</li>
                <li><strong>月份连续性:</strong> 系统会检查并提示月份缺失情况</li>
                <li><strong>统计意义:</strong> 重叠牛只<20头时会显示统计警告</li>
                <li><strong>计算透明度:</strong> 表格中显示每个指标的详细计算过程</li>
            </ul>
        </div>
        """
    
    def toggle_widget_visibility(self, widget):
        """切换控件显示/隐藏状态"""
        if widget.isVisible():
            widget.hide()
        else:
            widget.show()
    
    def create_result_panel(self):
        """创建右侧结果面板"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 自适应标签页样式
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        
        tab_font_size = self.get_dpi_scaled_font_size(16)  # 主标签页统一为16px
        tab_padding_v = max(int(10 * dpi_ratio * 0.6), 8)
        tab_padding_h = max(int(14 * dpi_ratio * 0.6), 10)
        tab_border_radius = max(int(5 * dpi_ratio * 0.6), 4)
        tab_min_width = 120  # 与左侧标签宽度统一
        
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #e0e0e0;
                border-radius: {tab_border_radius}px;
                background-color: white;
                margin-top: -1px;
            }}
            QTabBar::tab {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: 2px;
                border-top-left-radius: {tab_border_radius}px;
                border-top-right-radius: {tab_border_radius}px;
                font-size: {tab_font_size}px;
                font-weight: 500;
                color: #495057;
                min-width: {tab_min_width}px;
                min-height: 35px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 1px solid white;
                color: #007bff;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: #e9ecef;
            }}
        """)
        layout.addWidget(self.tab_widget)
        
        # 文件信息标签页
        self.file_info_widget = QTextEdit()
        self.file_info_widget.setReadOnly(True)
        info_font_size = 13  # 统一字体大小为13px
        info_padding = max(int(12 * dpi_ratio * 0.6), 10)
        self.file_info_widget.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                background-color: #f8f9fa;
                color: black;  /* 强制使用黑色字体 */
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {info_font_size}px;
                padding: {info_padding}px;
                line-height: 1.5;
            }}
        """)
        self.tab_widget.addTab(self.file_info_widget, "📁 文件信息")
        
        # 处理过程标签页
        self.process_log_widget = QTextEdit()
        self.process_log_widget.setReadOnly(True)
        self.process_log_widget.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                background-color: #f8f9fa;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {info_font_size}px;
                padding: {info_padding}px;
                line-height: 1.5;
                color: black;  /* 强制使用黑色字体 */
            }}
        """)
        # 设置初始内容
        self.process_log_widget.setText("🔄 处理过程日志\n\n等待开始处理文件...\n")
        self.tab_widget.addTab(self.process_log_widget, "🔄 处理过程")
        
        # 筛选结果标签页
        self.result_table = QTableWidget()
        table_font_size = max(int(14 * dpi_ratio * 0.8), 12)
        table_padding = max(int(8 * dpi_ratio * 0.6), 6)
        header_padding = max(int(10 * dpi_ratio * 0.6), 8)
        self.result_table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background-color: white;
                gridline-color: #e0e0e0;
                font-size: {table_font_size}px;
            }}
            QTableWidget::item {{
                padding: {table_padding}px;
                border-bottom: 1px solid #f0f0f0;
            }}
            QTableWidget::item:selected {{
                background-color: #e3f2fd;
                color: #1976d2;
            }}
            QHeaderView::section {{
                background-color: #f8f9fa;
                padding: {header_padding}px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
                color: #495057;
            }}
        """)
        # 创建筛选结果的次级标签页结构
        self.result_widget = self.create_result_sub_tabs()
        self.tab_widget.addTab(self.result_widget, "📊 筛选结果")
        
        # 筛选分析标签页（合并统计信息）
        self.analysis_widget = self.create_analysis_panel()
        self.tab_widget.addTab(self.analysis_widget, "🎯 筛选分析")
        
        return panel
    
    def create_result_sub_tabs(self):
        """创建筛选结果的次级标签页"""
        result_widget = QWidget()
        layout = QVBoxLayout(result_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建次级标签页容器
        self.result_sub_tabs = QTabWidget()
        # 获取DPI缩放比例
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        sub_tab_min_width = max(int(100 * dpi_ratio * 0.6), 80)  # 次级标签页最小宽度
        
        self.result_sub_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background-color: white;
            }}
            QTabBar::tab {{
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                padding: 10px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 13px;
                min-width: 100px;
                min-height: 30px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom-color: white;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: #e9ecef;
            }}
        """)
        
        # 次级标签页1: DHI基础筛选结果 (保留原有的结果表格)
        self.result_table = QTableWidget()
        self.result_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #dee2e6;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
                color: #495057;
            }
        """)
        self.result_sub_tabs.addTab(self.result_table, "📊 DHI基础筛选")
        
        # 次级标签页2: 慢性乳房炎筛查结果
        self.create_mastitis_screening_result_tab()
        
        # 次级标签页3: 隐性乳房炎监测
        self.create_mastitis_monitoring_result_tab()
        
        # 次级标签页4: 尿素氮追踪
        self.create_urea_tracking_result_tab()
        
        layout.addWidget(self.result_sub_tabs)
        return result_widget
    
    def create_mastitis_screening_result_tab(self):
        """创建慢性乳房炎筛查结果标签页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # 直接创建表格，不添加任何其他组件
        self.mastitis_screening_table = QTableWidget()
        self.mastitis_screening_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #ffeaa7;
                color: #2d3436;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        # 添加空状态提示
        self.mastitis_screening_table.setRowCount(1)
        self.mastitis_screening_table.setColumnCount(1)
        self.mastitis_screening_table.setHorizontalHeaderLabels(["状态"])
        
        empty_item = QTableWidgetItem("暂无筛查结果，请在左侧'慢性乳房炎筛查'功能中进行筛查")
        empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mastitis_screening_table.setItem(0, 0, empty_item)
        
        # 直接添加表格到布局，不使用卡片容器
        tab_layout.addWidget(self.mastitis_screening_table)
        
        self.result_sub_tabs.addTab(tab_widget, "🏥 慢性乳房炎筛查")
    
    def create_mastitis_monitoring_result_tab(self):
        """创建隐性乳房炎监测结果标签页"""
        # 检查PyQtGraph依赖
        try:
            import pyqtgraph as pg
        except ImportError:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            error_label = QLabel("缺少PyQtGraph依赖，请安装: pip install pyqtgraph")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #dc3545; padding: 20px;")
            tab_layout.addWidget(error_label)
            tab_layout.addStretch()
            self.result_sub_tabs.addTab(tab_widget, "👁️ 隐形乳房炎监测")
            return

        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(5)
        tab_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加说明信息
        info_label = QLabel("💡 请在左侧【隐形乳房炎月度监测】标签页中进行配置和分析，结果将在此处显示")
        info_label.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 12px;
                padding: 8px 12px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border-left: 4px solid #17a2b8;
                margin-bottom: 10px;
                font-weight: bold;
            }
        """)
        tab_layout.addWidget(info_label)
        
        # 创建主要内容区域 - 水平分割：左侧表格、右侧图表和公式说明
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setSizes([600, 400])  # 左侧表格600，右侧400
        
        # 左侧：监测结果表格
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 5, 0)
        
        table_title = QLabel("📊 监测结果")
        table_title.setStyleSheet("font-weight: bold; font-size: 14px; color: black; background-color: white; margin-bottom: 8px;")
        table_layout.addWidget(table_title)
        
        self.mastitis_monitoring_table = QTableWidget()
        self.mastitis_monitoring_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                background-color: white;
                gridline-color: #e0e0e0;
                alternate-background-color: #f8f9fa;
                color: black;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e0e0e0;
                color: black;
                background-color: white;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
                font-size: 11px;
                color: black;
            }
        """)
        table_layout.addWidget(self.mastitis_monitoring_table)
        
        # 右侧：图表和公式说明的垂直分割
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(3, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # 上部：趋势图表
        if ChinesePlotWidget:
            self.mastitis_monitoring_plot = ChinesePlotWidget()
        else:
            self.mastitis_monitoring_plot = pg.PlotWidget()
        self.mastitis_monitoring_plot.setLabel('left', '百分比 (%)')
        self.mastitis_monitoring_plot.setLabel('bottom', '月份')
        self.mastitis_monitoring_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mastitis_monitoring_plot.setBackground('white')
        self.mastitis_monitoring_plot.addLegend()
        self.mastitis_monitoring_plot.setMinimumHeight(250)
        
        right_layout.addWidget(self.mastitis_monitoring_plot)
        
        # 下部：可折叠的公式说明
        formula_container = QWidget()
        formula_layout = QVBoxLayout(formula_container)
        formula_layout.setContentsMargins(0, 5, 0, 0)
        
        # 公式标题和折叠按钮
        formula_header = QHBoxLayout()
        formula_title = QLabel("📖 公式说明")
        formula_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        
        self.formula_toggle_btn = QPushButton("▼ 展开")
        self.formula_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #3498db;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
            }
            QPushButton:hover {
                color: #2980b9;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        self.formula_toggle_btn.clicked.connect(self.toggle_monitoring_formula_visibility)
        
        formula_header.addWidget(formula_title)
        formula_header.addStretch()
        formula_header.addWidget(self.formula_toggle_btn)
        formula_layout.addLayout(formula_header)
        
        # 公式内容（初始隐藏）
        self.monitoring_formula_widget = QTextEdit()
        self.monitoring_formula_widget.setReadOnly(True)
        self.monitoring_formula_widget.setMaximumHeight(180)
        self.monitoring_formula_widget.setHtml(self.get_mastitis_monitoring_formula_html())
        self.monitoring_formula_widget.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                background-color: #f8f9fa;
                font-family: 'Arial', sans-serif;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.monitoring_formula_widget.setVisible(False)  # 初始隐藏
        formula_layout.addWidget(self.monitoring_formula_widget)
        
        right_layout.addWidget(formula_container)
        
        # 添加到主分割器
        main_splitter.addWidget(table_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([350, 450])  # 表格适中，右侧较宽
        
        tab_layout.addWidget(main_splitter)
        
        # 初始化变量
        self.mastitis_monitoring_calculator = None
        self.mastitis_monitoring_results = None
        
        self.result_sub_tabs.addTab(tab_widget, "👁️ 隐形乳房炎监测")
    
    def create_analysis_panel(self):
        """创建筛选分析面板（包含统计信息）"""
        panel = QWidget()
        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建垂直分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分：统计卡片
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        # 标题
        title_label = QLabel("筛选结果分析")
        title_font = QFont()
        title_font.setPointSize(max(int(14 * 0.6), 12))
        title_font.setBold(True)
        title_label.setFont(title_font)
        top_layout.addWidget(title_label)
        
        # 统计卡片容器
        cards_widget = QWidget()
        cards_layout = QHBoxLayout(cards_widget)
        
        # 创建4个统计卡片
        self.total_data_card = self.create_stat_card("全部数据", "0", "所有上传文件的牛头数", "#3498db")
        self.range_data_card = self.create_stat_card("筛选范围", "0", "选中文件的牛头数", "#17a2b8")
        self.result_data_card = self.create_stat_card("筛选结果", "0", "符合条件的牛头数", "#28a745")
        self.rate_data_card = self.create_stat_card("筛选率", "0%", "符合条件占全部数据比例", "#ffc107")
        
        cards_layout.addWidget(self.total_data_card)
        cards_layout.addWidget(self.range_data_card)
        cards_layout.addWidget(self.result_data_card)
        cards_layout.addWidget(self.rate_data_card)
        
        top_layout.addWidget(cards_widget)
        top_layout.addStretch()
        
        # 下半部分：统计信息选项卡
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建统计信息标签页
        self.stats_tab_widget = QTabWidget()
        
        # 获取屏幕DPI信息用于样式
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        
        tab_font_size = 13  # 与其他次级标签页一致
        tab_padding_v = 10
        tab_padding_h = 16
        tab_border_radius = 4
        tab_min_width = 100  # 与其他次级标签页一致
        
        self.stats_tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #bee5eb;
                border-radius: {tab_border_radius}px;
                background-color: white;
                margin-top: -1px;
            }}
            QTabBar::tab {{
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: 2px;
                border-top-left-radius: {tab_border_radius}px;
                border-top-right-radius: {tab_border_radius}px;
                font-size: {tab_font_size}px;
                font-weight: 500;
                color: #0c5460;
                min-width: {tab_min_width}px;
                min-height: 30px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 1px solid white;
                color: #007bff;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: #b8daff;
            }}
        """)
        
        # 创建各个统计选项卡
        self.create_statistics_tabs()
        
        bottom_layout.addWidget(self.stats_tab_widget)
        
        # 添加到分割器
        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        
        # 设置分割器初始大小比例 (卡片区域:统计信息区域 = 1:2)
        splitter.setSizes([150, 300])
        splitter.setCollapsible(0, False)  # 卡片区域不可完全折叠
        splitter.setCollapsible(1, False)  # 统计信息区域不可完全折叠
        
        # 设置分割器样式
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                border: 1px solid #ced4da;
                margin: 2px;
            }
            QSplitter::handle:horizontal {
                width: 3px;
            }
            QSplitter::handle:vertical {
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #007bff;
            }
        """)
        
        main_layout.addWidget(splitter)
        
        return panel
    
    def create_statistics_tabs(self, enabled_traits=None):
        """创建统计信息的各个选项卡
        
        Args:
            enabled_traits: 启用的性状列表，如果为None则创建默认选项卡
        """
        # 清空现有选项卡
        self.stats_tab_widget.clear()
        
        # 获取屏幕DPI信息
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        stats_font_size = 13  # 统一字体大小为13px
        stats_padding = max(int(8 * dpi_ratio * 0.6), 6)
        
        # 通用文本框样式
        text_style = f"""
            QTextEdit {{
                border: 1px solid #bee5eb;
                border-radius: 4px;
                background-color: white;
                color: black;  /* 强制使用黑色字体 */
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {stats_font_size}px;
                padding: {stats_padding}px;
                line-height: 1.4;
            }}
        """
        
        # 1. 总体统计标签页（始终显示）
        self.overall_stats_widget = QTextEdit()
        self.overall_stats_widget.setReadOnly(True)
        self.overall_stats_widget.setStyleSheet(text_style)
        self.overall_stats_widget.setText("📊 总体统计信息\n\n请先处理文件并进行筛选，然后查看统计结果。")
        self.stats_tab_widget.addTab(self.overall_stats_widget, "📊 总体统计")
        
        # 胎次分析（始终显示）
        self.parity_stats_widget = QTextEdit()
        self.parity_stats_widget.setReadOnly(True)
        self.parity_stats_widget.setStyleSheet(text_style)
        self.parity_stats_widget.setText("🐄 胎次分析\n\n等待筛选结果...")
        self.stats_tab_widget.addTab(self.parity_stats_widget, "🐄 胎次分析")
        
        # 动态创建性状选项卡字典，用于存储各种性状的分析widget
        self.trait_stats_widgets = {}
        
        # 如果提供了启用的性状列表，则动态创建对应选项卡
        if enabled_traits:
            # 定义性状的图标和中文名称映射
            trait_config = {
                'protein_pct': {'icon': '🥛', 'name': '蛋白率分析'},
                'somatic_cell_count': {'icon': '🔬', 'name': '体细胞数分析'},
                'fat_pct': {'icon': '🧈', 'name': '乳脂率分析'},
                'lactose_pct': {'icon': '🍬', 'name': '乳糖率分析'},
                'milk_yield': {'icon': '🥛', 'name': '产奶量分析'},
                'lactation_days': {'icon': '📅', 'name': '泌乳天数分析'},
                'solids_pct': {'icon': '🧪', 'name': '固形物分析'},
                'fat_protein_ratio': {'icon': '⚖️', 'name': '脂蛋比分析'},
                'urea_nitrogen': {'icon': '🧬', 'name': '尿素氮分析'},
                'total_fat_pct': {'icon': '🧈', 'name': '总乳脂分析'},
                'total_protein_pct': {'icon': '🥛', 'name': '总蛋白分析'},
                'mature_equivalent': {'icon': '🐄', 'name': '成年当量分析'},
                'somatic_cell_score': {'icon': '🔬', 'name': '体细胞分分析'},
                'freezing_point': {'icon': '❄️', 'name': '冰点分析'},
                'total_bacterial_count': {'icon': '🦠', 'name': '细菌总数分析'},
                'dry_matter_intake': {'icon': '🌾', 'name': '干物质采食量分析'},
                'net_energy_lactation': {'icon': '⚡', 'name': '泌乳净能分析'},
                'metabolizable_protein': {'icon': '🧬', 'name': '可代谢蛋白分析'},
                'crude_protein': {'icon': '🫘', 'name': '粗蛋白分析'},
                'neutral_detergent_fiber': {'icon': '🌾', 'name': '中性洗涤纤维分析'},
                'acid_detergent_fiber': {'icon': '🌾', 'name': '酸性洗涤纤维分析'},
                'starch': {'icon': '🌽', 'name': '淀粉分析'},
                'ether_extract': {'icon': '🧪', 'name': '醚提取物分析'},
                'ash': {'icon': '🔥', 'name': '灰分分析'},
                'calcium': {'icon': '🦴', 'name': '钙分析'},
                'phosphorus': {'icon': '⚗️', 'name': '磷分析'},
                'magnesium': {'icon': '🧪', 'name': '镁分析'},
                'sodium': {'icon': '🧂', 'name': '钠分析'},
                'potassium': {'icon': '🍌', 'name': '钾分析'},
                'sulfur': {'icon': '💛', 'name': '硫分析'}
            }
            
            # 为每个启用的性状创建选项卡
            for trait in enabled_traits:
                if trait in trait_config:
                    config = trait_config[trait]
                    widget = QTextEdit()
                    widget.setReadOnly(True)
                    widget.setStyleSheet(text_style)
                    widget.setText(f"{config['icon']} {config['name']}\n\n等待筛选结果...")
                    
                    self.trait_stats_widgets[trait] = widget
                    self.stats_tab_widget.addTab(widget, f"{config['icon']} {config['name']}")
        
        else:
            # 默认选项卡（兼容旧版本）
            # 蛋白率分析标签页
            self.protein_stats_widget = QTextEdit()
            self.protein_stats_widget.setReadOnly(True)
            self.protein_stats_widget.setStyleSheet(text_style)
            self.protein_stats_widget.setText("🥛 蛋白率分析\n\n等待筛选结果...")
            self.stats_tab_widget.addTab(self.protein_stats_widget, "🥛 蛋白率分析")
            self.trait_stats_widgets['protein_pct'] = self.protein_stats_widget
            
            # 体细胞数分析标签页
            self.somatic_stats_widget = QTextEdit()
            self.somatic_stats_widget.setReadOnly(True)
            self.somatic_stats_widget.setStyleSheet(text_style)
            self.somatic_stats_widget.setText("🔬 体细胞数分析\n\n等待筛选结果...")
            self.stats_tab_widget.addTab(self.somatic_stats_widget, "🔬 体细胞数分析")
            self.trait_stats_widgets['somatic_cell_count'] = self.somatic_stats_widget
            
            # 其他性状分析标签页
            self.other_traits_stats_widget = QTextEdit()
            self.other_traits_stats_widget.setReadOnly(True)
            self.other_traits_stats_widget.setStyleSheet(text_style)
            self.other_traits_stats_widget.setText("📈 其他性状分析\n\n等待筛选结果...")
            self.stats_tab_widget.addTab(self.other_traits_stats_widget, "📈 其他性状")
        
        # 计算方法说明标签页（始终显示）
        method_widget = QTextEdit()
        method_widget.setReadOnly(True)
        method_widget.setStyleSheet(text_style)
        method_text = """📋 计算方法说明

🔢 基础统计：
• 牛头数统计基于'牛场编号+管理号'的唯一组合
• 筛选率 = 符合条件的牛头数 ÷ 全部数据的牛头数 × 100%

🥛 蛋白率计算：
• 单头牛平均蛋白率 = Σ(单次蛋白率×单次产奶量) / Σ(单次产奶量)
• 当月所有牛平均蛋白率 = Σ(各牛当月蛋白率×各牛当月产奶量) / Σ(各牛当月产奶量)
• 总体平均蛋白率 = Σ(所有记录蛋白率×所有记录产奶量) / Σ(所有记录产奶量)
• 采用产奶量加权平均的方式计算平均蛋白率，而非简单算术平均

🔬 体细胞数计算：
• 体细胞数以万/ml为单位
• 月度平均值采用算术平均
• 筛选时支持空值判断处理

🐄 胎次分析：
• 胎次为最后一次取样时的胎次
• 群体平均胎次采用算术平均
• 支持按胎次范围筛选

📊 月度分析：
• 按时间顺序展示各月份数据统计
• 显示数据范围和平均值
• 支持多性状同步分析
"""
        method_widget.setText(method_text)
        self.stats_tab_widget.addTab(method_widget, "📋 计算方法")
        
        # 保留原始的stats_widget引用以便兼容现有代码
        self.stats_widget = self.overall_stats_widget
    
    def create_stat_card(self, title, value, description, color):
        """创建统计卡片"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_title_font_size = max(int(11 * 0.6), 10)
        title_label.setStyleSheet(f"color: black; background-color: white; font-size: {card_title_font_size}px; margin-bottom: 5px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 数值
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_value_font_size = max(int(28 * 0.6), 20)
        value_label.setStyleSheet(f"color: {color}; font-size: {card_value_font_size}px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(value_label)
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_desc_font_size = max(int(10 * 0.6), 9)
        desc_label.setStyleSheet(f"color: #495057; font-size: {card_desc_font_size}px; font-weight: 500;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 保存value_label引用以便后续更新
        setattr(card, 'value_label', value_label)
        
        return card
    
    def load_config(self):
        """加载配置"""
        try:
            with open("config.yaml", "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except:
            self.config = {}
    
    def select_files(self):
        """选择文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "选择DHI报告文件",
            "",
            "支持的文件 (*.zip *.xlsx *.xls);;ZIP文件 (*.zip);;Excel文件 (*.xlsx *.xls)"
        )
        
        if files:
            # 更新传统文件列表（保持兼容性）
            self.file_list.clear()
            self.selected_files = files
            
            for file in files:
                filename = os.path.basename(file)
                item = QListWidgetItem(filename)
                self.file_list.addItem(item)
            
            # 更新新的文件标签显示
            self.update_file_tags_display(files)
            
            self.process_btn.setEnabled(True)
            self.safe_show_status_message(f"已选择 {len(files)} 个文件")
    
    def update_file_tags_display(self, files):
        """更新文件标签显示"""
        if not hasattr(self, 'file_tags_layout'):
            return
        
        # 清除所有现有的文件标签
        for i in reversed(range(self.file_tags_layout.count())):
            item = self.file_tags_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
        
        # 为每个文件创建标签
        for file_path in files:
            filename = os.path.basename(file_path)
            file_tag = self.create_file_tag(filename)
            self.file_tags_layout.addWidget(file_tag)
        
        # 添加弹性空间
        self.file_tags_layout.addStretch()
    
    def create_file_tag(self, filename):
        """创建文件标签"""
        tag_widget = QWidget()
        tag_widget.setMaximumHeight(self.get_dpi_scaled_size(36))  # 进一步增大高度为36px，更易阅读
        tag_widget.setStyleSheet("""
            QWidget {
                background-color: #e9f4ff;
                border: 1px solid #007bff;
                border-radius: 12px;
                margin: 2px;
            }
        """)
        
        tag_layout = QHBoxLayout(tag_widget)
        tag_layout.setContentsMargins(12, 6, 12, 6)  # 进一步增大内边距
        tag_layout.setSpacing(8)  # 进一步增大间距
        
        # 文件图标
        file_icon = QLabel("📄")
        file_icon.setStyleSheet("background: transparent; border: none; font-size: 14px;")
        tag_layout.addWidget(file_icon)
        
        # 文件名 - 支持文本换行和完整显示
        file_label = QLabel(filename)
        file_label.setStyleSheet("background: transparent; border: none; font-size: 13px; color: #0056b3;")
        file_label.setWordWrap(True)  # 允许文本换行
        file_label.setMinimumWidth(self.get_dpi_scaled_size(200))  # 设置最小宽度确保文本有足够空间
        file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # 允许水平扩展
        tag_layout.addWidget(file_label)
        
        tag_layout.addStretch()
        
        return tag_widget
    
    def clear_files(self):
        """清空已选择的文件"""
        if hasattr(self, 'file_list'):
            self.file_list.clear()
        
        # 清空文件标签显示
        if hasattr(self, 'file_tags_layout'):
            # 清除所有现有的文件标签
            for i in reversed(range(self.file_tags_layout.count())):
                item = self.file_tags_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
            
            # 恢复"尚未选择文件"提示
            no_files_label = QLabel("尚未选择文件")
            no_files_label.setStyleSheet("color: #9ca3af; font-size: 11px; font-style: italic;")
            self.file_tags_layout.addWidget(no_files_label)
            self.file_tags_layout.addStretch()
        
        # 重置状态
        self.selected_files = []
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.safe_show_status_message("已清空所有文件")
    
    def process_files(self):
        """处理文件"""
        if not hasattr(self, 'selected_files') or not self.selected_files:
            return
        
        self.process_btn.setEnabled(False)
        
        # 创建增强进度条对话框（使用新的流畅进度条）
        self.file_progress_dialog = SmoothProgressDialog(
            "正在处理文件...",
            "取消",
            0, 100,
            self
        )
        self.file_progress_dialog.setWindowTitle("文件处理")
        self.file_progress_dialog.canceled.connect(self.cancel_file_processing)
        self.file_progress_dialog.show()
        
        # 启动处理线程
        filenames = [os.path.basename(f) for f in self.selected_files]
        self.process_thread = FileProcessThread(self.selected_files, filenames, self.urea_tracker)
        self.process_thread.progress_updated.connect(self.update_file_progress)
        self.process_thread.file_processed.connect(self.file_processed)
        self.process_thread.processing_completed.connect(self.processing_completed)
        self.process_thread.log_updated.connect(self.update_process_log)
        self.process_thread.start()
        
        # 切换到处理过程标签页
        self.tab_widget.setCurrentWidget(self.process_log_widget)
    
    def update_file_progress(self, status, progress):
        """更新文件处理进度"""
        if hasattr(self, 'file_progress_dialog'):
            self.file_progress_dialog.setValue(progress)
            self.file_progress_dialog.setLabelText(status)
        self.statusBar().showMessage(status)
    
    def cancel_file_processing(self):
        """取消文件处理"""
        if hasattr(self, 'process_thread') and self.process_thread.isRunning():
            self.process_thread.terminate()
            self.process_thread.wait()
            self.process_btn.setEnabled(True)
            self.statusBar().showMessage("文件处理已取消")
    
    def update_progress(self, status, progress):
        """更新进度（兼容旧代码）"""
        # 不更新progress_label，只更新进度条和状态栏
        self.progress_bar.setValue(progress)
        self.statusBar().showMessage(status)
    
    def update_process_log(self, log_message):
        """更新处理过程日志"""
        # 在日志末尾添加新消息
        self.process_log_widget.append(log_message)
        # 滚动到底部
        cursor = self.process_log_widget.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.process_log_widget.setTextCursor(cursor)
    
    def file_processed(self, filename, success, message, file_info):
        """单个文件处理完成"""
        if success:
            info = f"✅ {filename}: {message}"
        else:
            info = f"❌ {filename}: {message}"
        
        self.file_info_widget.append(info)
        self.statusBar().showMessage(f"已处理: {filename}")
        
        # 移除单独处理缺少牛场编号的逻辑，改为在批量处理完成时统一处理
    
    # handle_missing_farm_id and add_farm_id_to_data methods removed - no longer needed for single-farm uploads
    
    def processing_completed(self, results):
        """所有文件处理完成"""
        # 关闭进度条对话框
        if hasattr(self, 'file_progress_dialog'):
            self.file_progress_dialog.close()
        
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        
        # 直接完成处理，无需检查牧场编号
        self.complete_processing(results)
    
    # handle_batch_missing_farm_id method removed - no longer needed for single-farm uploads
    
    # check_and_handle_farm_id_consistency method removed - no longer needed for single-farm uploads
    
    def complete_processing(self, results):
        """完成处理流程"""
        # 保存数据
        self.data_list = results['all_data']
        
        # 处理成功后设置标志
        self.dhi_processed_ok = True if self.data_list else False
        
        # 计算总牛头数并更新分析面板
        total_cows = set()
        all_data_combined = []
        
        for item in self.data_list:
            df = item['data']
            if df is not None and not df.empty:
                all_data_combined.append(df)
                if 'management_id' in df.columns:
                    cow_ids = df['management_id'].dropna().unique()
                    for cow_id in cow_ids:
                        total_cows.add(cow_id)
        
        # 合并所有数据用于分析
        if all_data_combined:
            combined_df = pd.concat(all_data_combined, ignore_index=True)
            self.update_filter_ranges(combined_df)
        
        # 更新全部数据统计
        getattr(self.total_data_card, 'value_label').setText(str(len(total_cows)))
        
        # 牛场编号选择器已移除 - 单牛场上传不再需要
        
        # 检测重复文件并在文件信息框显示
        self.detect_and_display_duplicates()
        
        # 显示处理结果
        success_count = len(results.get('success_files', []))
        failed_count = len(results.get('failed_files', []))
        summary = f"\n📊 处理完成！\n"
        summary += f"成功: {success_count} 个文件\n"
        summary += f"失败: {failed_count} 个文件\n\n"
        
        self.file_info_widget.append(summary)
        
        # 启用筛选按钮（如果存在）
        if success_count > 0 and hasattr(self, 'filter_btn'):
            self.filter_btn.setEnabled(True)
        
        status_msg = f"处理完成：成功 {success_count} 个，失败 {failed_count} 个"
        self.statusBar().showMessage(status_msg)
        
        # 提取并更新慢性感染牛识别的月份选择（如果有DHI数据）
        dhi_months = set()
        for item in self.data_list:
            df = item['data']
            if 'sample_date' in df.columns and 'somatic_cell_count' in df.columns:
                # 从有体细胞数据的文件中提取月份
                dates = pd.to_datetime(df['sample_date'], errors='coerce').dropna()
                months = dates.dt.strftime('%Y年%m月').unique()
                dhi_months.update(months)
        
        if dhi_months:
            sorted_months = sorted(list(dhi_months))
            print(f"从DHI数据中提取到月份: {sorted_months}")
            self.update_chronic_months_options(sorted_months)
        else:
            print("未找到包含体细胞数据的DHI文件，无法更新月份选择")
        
        # 如果尿素氮追踪器有数据，启用分析按钮
        if hasattr(self, 'urea_analyze_btn') and self.urea_tracker.dhi_data_dict:
            self.urea_analyze_btn.setEnabled(True)
    
    def detect_and_display_duplicates(self):
        """检测重复文件并在文件信息框中显示详细信息"""
        if not self.data_list or len(self.data_list) < 2:
            return
        
        try:
            # 使用处理器的重复检测功能
            duplicate_result = self.processor.detect_duplicate_data(self.data_list)
            
            if duplicate_result['has_duplicates']:
                duplicate_count = duplicate_result['duplicate_files_count']
                group_count = len(duplicate_result['duplicate_groups'])
                
                self.file_info_widget.append(f"\n⚠️ 重复文件检测结果:")
                self.file_info_widget.append(f"发现 {group_count} 组重复文件，共涉及 {duplicate_count} 个文件\n")
                
                for i, group in enumerate(duplicate_result['duplicate_groups'], 1):
                    self.file_info_widget.append(f"📋 重复组 {i}:")
                    
                    for j, file_info in enumerate(group):
                        filename = file_info['filename']
                        data = file_info['data']
                        
                        # 获取文件的月份信息
                        months_info = self._extract_file_months_info(data)
                        similarity_score = file_info.get('similarity_score', 'N/A')
                        
                        if j == 0:
                            # 第一个文件作为基准
                            self.file_info_widget.append(f"  📄 {filename}")
                            self.file_info_widget.append(f"     📅 数据月份: {months_info}")
                        else:
                            # 后续文件显示与基准的相似度
                            self.file_info_widget.append(f"  📄 {filename} (相似度: {similarity_score:.1%})")
                            self.file_info_widget.append(f"     📅 数据月份: {months_info}")
                    
                    self.file_info_widget.append("")  # 空行分隔不同组
                
                self.file_info_widget.append("💡 建议: 检查这些重复文件的内容，确认是否需要保留所有文件。\n")
                
        except Exception as e:
            print(f"重复文件检测时出错: {e}")
            # 不影响主流程，只记录错误
            self.file_info_widget.append(f"\n⚠️ 重复文件检测时出现错误: {str(e)}\n")
    
    def _extract_file_months_info(self, df):
        """从数据框中提取月份信息"""
        try:
            if 'sample_date' not in df.columns:
                return "未知月份"
            
            # 转换日期并提取月份
            dates = pd.to_datetime(df['sample_date'], errors='coerce').dropna()
            if dates.empty:
                return "无有效日期"
            
            # 获取年月信息
            year_months = dates.dt.strftime('%Y年%m月').unique()
            
            if len(year_months) == 1:
                return year_months[0]
            elif len(year_months) <= 3:
                return "、".join(sorted(year_months))
            else:
                sorted_months = sorted(year_months)
                return f"{sorted_months[0]}～{sorted_months[-1]} (共{len(year_months)}个月)"
                
        except Exception as e:
            print(f"提取月份信息时出错: {e}")
            return "月份信息提取失败"
    
    def update_filter_ranges(self, df):
        """根据数据更新筛选条件的范围和默认值"""
        try:
            # 使用新的数据范围计算功能
            data_ranges = self.processor.get_data_ranges(self.data_list)
            self.current_data_ranges = data_ranges  # 保存数据范围供后续使用
            
            # 计算月数上限
            max_months = data_ranges.get('months', {}).get('max', 12)
            
            print(f"数据范围计算完成：")
            print(f"  月数范围: 0 - {max_months}个月")
            for field, range_info in data_ranges.items():
                if field != 'months' and isinstance(range_info, dict):
                    print(f"  {field}: {range_info.get('description', '未知')}")
            
            # 更新胎次范围
            if 'parity' in data_ranges:
                parity_range = data_ranges['parity']
                min_parity = int(parity_range['min'])
                max_parity = int(parity_range['max'])
                
                # 更新胎次控件（如果存在）
                if hasattr(self, 'parity_min') and hasattr(self, 'parity_max'):
                    # 更新范围 - 使用实际数据范围但不设置上限
                    self.parity_min.setRange(min_parity, 99)
                    self.parity_max.setRange(min_parity, 99)
                    
                    # 设置默认值为数据范围
                    self.parity_min.setValue(min_parity)
                    self.parity_max.setValue(max_parity)
            
                print(f"  胎次控件更新: {min_parity}-{max_parity}胎")
            
            # 更新蛋白率筛选控件（如果存在）
            if hasattr(self, 'protein_min') and 'protein_pct' in data_ranges:
                protein_range = data_ranges['protein_pct']
                
                # 设置范围 - 移除人为上限限制
                self.protein_min.setRange(0.0, 999999.99)
                self.protein_max.setRange(0.0, 999999.99)
                
                # 使用实际数据的最小值和最大值
                actual_min = protein_range['min']
                actual_max = protein_range['max']
                self.protein_min.setValue(actual_min)
                self.protein_max.setValue(actual_max)
                
                # 更新最少符合月数范围
                if hasattr(self, 'protein_months'):
                    self.protein_months.setRange(0, max_months)
                    self.protein_months.setValue(min(3, max_months // 2) if max_months > 0 else 1)
                
                print(f"  蛋白率控件更新: {actual_min}-{actual_max}% (实际数据范围)")
            
            # 更新体细胞数筛选控件（如果存在）
            if hasattr(self, 'somatic_min') and 'somatic_cell_count' in data_ranges:
                somatic_range = data_ranges['somatic_cell_count']
                
                # 设置范围 - 移除人为上限限制
                self.somatic_min.setRange(0.0, 999999.99)
                self.somatic_max.setRange(0.0, 999999.99)
                
                # 使用实际数据的最小值和最大值
                actual_min = somatic_range['min']
                actual_max = somatic_range['max']
                self.somatic_min.setValue(actual_min)
                self.somatic_max.setValue(actual_max)
                
                # 更新最少符合月数范围
                if hasattr(self, 'somatic_months'):
                    self.somatic_months.setRange(0, max_months)
                    self.somatic_months.setValue(min(3, max_months // 2) if max_months > 0 else 1)
                
                print(f"  体细胞数控件更新: {actual_min}-{actual_max}万/ml (实际数据范围)")
            
            # 更新其他筛选项控件
            if hasattr(self, 'added_other_filters'):
                for filter_key, widget in self.added_other_filters.items():
                    if filter_key in data_ranges:
                        field_range = data_ranges[filter_key]
                        
                        # 使用实际数据的最小值和最大值
                        actual_min = field_range['min']
                        actual_max = field_range['max']
                        
                        # 更新数值范围 - 移除人为上限限制
                        widget.range_min.setRange(-999999.99, 999999.99)
                        widget.range_max.setRange(-999999.99, 999999.99)
                        widget.range_min.setValue(actual_min)
                        widget.range_max.setValue(actual_max)
                        
                        # 更新最少符合月数范围
                        widget.months_spinbox.setRange(0, max_months)
                        widget.months_spinbox.setValue(min(3, max_months // 2) if max_months > 0 else 1)
                        
                        print(f"  {filter_key}控件更新: {actual_min}-{actual_max} (实际数据范围)")
            
            # 更新日期范围
            if 'sample_date' in df.columns:
                date_data = pd.to_datetime(df['sample_date'], errors='coerce').dropna()
                if not date_data.empty:
                    min_date = date_data.min().date()
                    max_date = date_data.max().date()
                    
                    # 更新日期选择器（如果存在）
                    if hasattr(self, 'date_start') and hasattr(self, 'date_end'):
                        self.date_start.setDate(QDate(min_date))
                        self.date_end.setDate(QDate(max_date))
            
                    print(f"  日期范围更新: {min_date} 到 {max_date}")
            
            # 更新未来泌乳天数的默认值和范围
            if hasattr(self, 'future_days_min'):
                # 根据数据中的泌乳天数范围设置合理的未来泌乳天数范围
                if 'lactation_days' in data_ranges:
                    lactation_range = data_ranges['lactation_days']
                    # 未来泌乳天数通常在50-350天之间
                    self.future_days_min.setValue(50)
                    self.future_days_max.setValue(min(350, int(lactation_range['max'] * 1.2)))
                else:
                    self.future_days_min.setValue(50)
                    self.future_days_max.setValue(350)
            
            # 在状态栏显示数据范围摘要
            range_summary = f"数据跨越{max_months}个月"
            if 'protein_pct' in data_ranges:
                protein_info = data_ranges['protein_pct']
                range_summary += f"，蛋白率{protein_info['min']:.1f}-{protein_info['max']:.1f}%"
            if 'somatic_cell_count' in data_ranges:
                somatic_info = data_ranges['somatic_cell_count']
                range_summary += f"，体细胞数{somatic_info['min']:.1f}-{somatic_info['max']:.1f}万/ml"
            self.statusBar().showMessage(f"筛选条件已设置为实际数据范围 - {range_summary}")
            
        except Exception as e:
            print(f"更新筛选范围时出错: {e}")
            import traceback
            traceback.print_exc()
            # 如果出错，使用旧的逻辑作为备份
            self._update_filter_ranges_fallback(df)
    
    def _update_filter_ranges_fallback(self, df):
        """备用的范围更新逻辑"""
        try:
            # 原有的简单逻辑
            if 'parity' in df.columns:
                parity_data = df['parity'].dropna()
                if not parity_data.empty:
                    min_parity = int(parity_data.min())
                    max_parity = int(parity_data.max())
                    
                    if hasattr(self, 'parity_min') and hasattr(self, 'parity_max'):
                        self.parity_min.setRange(min_parity, 99)
                        self.parity_max.setRange(min_parity, 99)
                        self.parity_min.setValue(min_parity)
                        self.parity_max.setValue(max_parity)
            
            # 更新蛋白率筛选控件（备用逻辑）
            if 'protein_pct' in df.columns and hasattr(self, 'protein_min'):
                protein_data = df['protein_pct'].dropna()
                if not protein_data.empty:
                    min_protein = float(protein_data.min())
                    max_protein = float(protein_data.max())
                    
                    self.protein_min.setRange(0.0, 999999.99)
                    self.protein_max.setRange(0.0, 999999.99)
                    self.protein_min.setValue(min_protein)
                    self.protein_max.setValue(max_protein)
                    print(f"  蛋白率控件更新(备用): {min_protein}-{max_protein}% (实际数据范围)")
            
            # 更新体细胞数筛选控件（备用逻辑）
            if 'somatic_cell_count' in df.columns and hasattr(self, 'somatic_min'):
                somatic_data = df['somatic_cell_count'].dropna()
                if not somatic_data.empty:
                    min_somatic = float(somatic_data.min())
                    max_somatic = float(somatic_data.max())
                    
                    self.somatic_min.setRange(0.0, 999999.99)
                    self.somatic_max.setRange(0.0, 999999.99)
                    self.somatic_min.setValue(min_somatic)
                    self.somatic_max.setValue(max_somatic)
                    print(f"  体细胞数控件更新(备用): {min_somatic}-{max_somatic}万/ml (实际数据范围)")
            
            # 更新其他筛选项控件（备用逻辑）
            if hasattr(self, 'added_other_filters'):
                # 支持的数值字段列表
                numeric_fields = [
                    'fat_pct', 'lactose_pct', 'milk_yield', 'lactation_days', 'solids_pct',
                    'fat_protein_ratio', 'urea_nitrogen', 'total_fat_pct', 'total_protein_pct',
                    'mature_equivalent', 'somatic_cell_score', 'freezing_point', 'total_bacterial_count'
                ]
                
                for filter_key, widget in self.added_other_filters.items():
                    if filter_key in numeric_fields and filter_key in df.columns:
                        field_data = df[filter_key].dropna()
                        if not field_data.empty:
                            min_val = float(field_data.min())
                            max_val = float(field_data.max())
                            
                            widget.range_min.setRange(-999999.99, 999999.99)
                            widget.range_max.setRange(-999999.99, 999999.99)
                            widget.range_min.setValue(min_val)
                            widget.range_max.setValue(max_val)
                            print(f"  {filter_key}控件更新(备用): {min_val}-{max_val} (实际数据范围)")
            
            # 设置基本的月数范围
            if hasattr(self, 'protein_months'):
                self.protein_months.setRange(1, 12)
                self.protein_months.setValue(3)
                
        except Exception as e:
            print(f"备用范围更新也出错: {e}")
            # 最后的保险，设置最基本的默认值
            pass
    
    def start_filtering(self):
        """开始筛选"""
        # 重置筛选完成标志
        self._filtering_completed = False
        
        if not self.data_list:
            self.show_warning("警告", "请先处理文件")
            return
        
        # 构建筛选条件
        filters = self.build_filters()
        selected_files = [item['filename'] for item in self.data_list]
        
        # 检查是否有启用的特殊筛选项
        special_filters_enabled = False
        special_filter_names = []
        
        for filter_name, filter_config in filters.items():
            if (filter_name not in ['parity', 'date_range', 'future_lactation_days'] and 
                filter_config.get('enabled', False)):
                special_filters_enabled = True
                # 获取中文名称
                if filter_name == 'protein_pct':
                    special_filter_names.append('蛋白率')
                elif filter_name == 'somatic_cell_count':
                    special_filter_names.append('体细胞数')
                else:
                    # 从其他筛选项中获取中文名称
                    if hasattr(self, 'added_other_filters') and filter_name in self.added_other_filters:
                        widget = self.added_other_filters[filter_name]
                        special_filter_names.append(widget.chinese_name)
                    else:
                        special_filter_names.append(filter_name)
        
        if not special_filters_enabled:
            reply = QMessageBox.question(
                self, 
                "确认筛选", 
                "您没有启用任何特殊筛选项（蛋白率、体细胞数等），只会应用基础筛选条件。\n确定要继续吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        else:
            filter_list = "、".join(special_filter_names)
            reply = QMessageBox.question(
                self, 
                "确认筛选", 
                f"将应用以下筛选项：{filter_list}\n确定要开始筛选吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # 显示/隐藏按钮（如果存在）
        if hasattr(self, 'filter_btn'):
            self.filter_btn.setEnabled(False)
        
        # 创建增强进度条对话框（使用新的流畅进度条）
        self.filter_progress_dialog = SmoothProgressDialog(
            "正在筛选数据...",
            "取消",
            0, 100,
            self
        )
        self.filter_progress_dialog.setWindowTitle("数据筛选")
        self.filter_progress_dialog.canceled.connect(self.cancel_filtering)
        self.filter_progress_dialog.show()
        
        # 启动筛选线程（传递processor实例以共享在群牛数据）
        self.filter_thread = FilterThread(self.data_list, filters, selected_files, self.processor, self.urea_tracker)
        self.filter_thread.progress_updated.connect(self.update_filter_progress_dialog)
        self.filter_thread.filtering_completed.connect(self.filtering_completed)
        self.filter_thread.log_updated.connect(self.update_process_log)
        self.filter_thread.start()
        
        # 切换到处理过程标签页
        self.tab_widget.setCurrentWidget(self.process_log_widget)
    
    def build_filters(self):
        """构建筛选条件"""
        filters = {}
        
        # 牛场编号筛选已移除 - 单牛场上传模式
        
        # 胎次（如果控件存在）
        if hasattr(self, 'parity_min') and hasattr(self, 'parity_max'):
            filters['parity'] = {
                'field': 'parity',
                'enabled': True,
                'min': self.parity_min.value(),
                'max': self.parity_max.value()
            }
        else:
            # 使用默认值
            filters['parity'] = {
                'field': 'parity',
                'enabled': True,
                'min': 1,
                'max': 99
            }
        
        # 日期范围（如果控件存在）
        if hasattr(self, 'date_start') and hasattr(self, 'date_end'):
            filters['date_range'] = {
                'field': 'sample_date',
                'enabled': True,
                'start_date': self.date_start.date().toString("yyyy-MM-dd"),
                'end_date': self.date_end.date().toString("yyyy-MM-dd")
            }
        else:
            # 使用默认值（不限制日期）
            filters['date_range'] = {
                'field': 'sample_date',
                'enabled': False,
                'start_date': "1900-01-01",
                'end_date': "2099-12-31"
            }
        
        # 蛋白率筛选（新的独立筛选项）
        if hasattr(self, 'protein_enabled') and self.protein_enabled.isChecked():
            filters['protein_pct'] = {
                'field': 'protein_pct',
                'enabled': True,
                'min': self.protein_min.value(),
                'max': self.protein_max.value(),
                'min_match_months': self.protein_months.value(),
                'empty_handling': self.protein_empty.currentText()
            }
        
        # 体细胞数筛选（新的独立筛选项）
        if hasattr(self, 'somatic_enabled') and self.somatic_enabled.isChecked():
            filters['somatic_cell_count'] = {
                'field': 'somatic_cell_count',
                'enabled': True,
                'min': self.somatic_min.value(),
                'max': self.somatic_max.value(),
                'min_match_months': self.somatic_months.value(),
                'empty_handling': self.somatic_empty.currentText()
            }
        
        # 其他筛选项
        for filter_key, widget in self.added_other_filters.items():
            if widget.enabled_checkbox.isChecked():
                filters[filter_key] = {
                    'field': filter_key,
                    'enabled': True,
                    'min': widget.range_min.value(),
                    'max': widget.range_max.value(),
                    'min_match_months': widget.months_spinbox.value(),
                    'empty_handling': widget.empty_combo.currentText()
                }
        
        # 未来泌乳天数 - 根据复选框状态决定是否启用（如果控件存在）
        if hasattr(self, 'future_days_enabled') and hasattr(self, 'plan_date'):
            filters['future_lactation_days'] = {
                'field': 'future_lactation_days',
                'enabled': self.future_days_enabled.isChecked(),
                'min': self.future_days_min.value(),
                'max': self.future_days_max.value(),
                'plan_date': self.plan_date.date().toString("yyyy-MM-dd")
            }
        else:
            # 默认禁用未来泌乳天数筛选
            filters['future_lactation_days'] = {
                'field': 'future_lactation_days',
                'enabled': False,
                'min': 50,
                'max': 350,
                'plan_date': QDate.currentDate().addDays(30).toString("yyyy-MM-dd")
            }
        
        # 尿素氮追踪分析 - 不在基础筛选中执行
        # 尿素氮追踪有独立的"开始分析"按钮，不应在基础筛选中自动执行
        filters['urea_tracking'] = {
            'enabled': False  # 基础筛选不执行尿素氮追踪
        }
        
        return filters
    
    def update_filter_progress_dialog(self, status, progress):
        """更新筛选进度对话框"""
        if hasattr(self, 'filter_progress_dialog'):
            self.filter_progress_dialog.setValue(progress)
            self.filter_progress_dialog.setLabelText(status)
        self.statusBar().showMessage(status)
    
    def cancel_filtering(self):
        """取消筛选"""
        # 如果筛选已完成，直接返回
        if hasattr(self, '_filtering_completed') and self._filtering_completed:
            return
            
        # 检查是否有正在运行的筛选线程
        if hasattr(self, 'filter_thread') and self.filter_thread.isRunning():
            # 弹出确认对话框
            reply = QMessageBox.question(
                self,
                "确认取消",
                "确定要取消当前筛选吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.filter_thread.request_cancel()
                self.filter_thread.wait()
                if hasattr(self, 'filter_btn'):
                    self.filter_btn.setEnabled(True)
                self.statusBar().showMessage("数据筛选已取消")
    
    def update_filter_progress(self, status, progress):
        """更新筛选进度（兼容旧代码）"""
        if hasattr(self, 'filter_label'):
            self.filter_label.setText(status)
        if hasattr(self, 'filter_progress'):
            self.filter_progress.setValue(progress)
        self.statusBar().showMessage(status)
    
    def filtering_completed(self, success, message, results_df, stats=None):
        """筛选完成"""
        # 设置标志，表示筛选已完成
        self._filtering_completed = True
        
        # 关闭进度条对话框
        if hasattr(self, 'filter_progress_dialog'):
            # 先断开信号连接
            try:
                self.filter_progress_dialog.canceled.disconnect()
            except:
                pass
            self.filter_progress_dialog.close()
        
        self._reset_filter_ui_state()
        
        if success:
            # 调试：验证接收到的数据
            print(f"DEBUG: ===== 接收到的数据验证 =====")
            print(f"DEBUG: 接收到的results_df行数: {len(results_df)}")
            if not results_df.empty and '未来泌乳天数(天)' in results_df.columns:
                received_values = results_df['未来泌乳天数(天)'].dropna()
                if len(received_values) > 0:
                    print(f"DEBUG: 接收到的未来泌乳天数范围: {received_values.min()}-{received_values.max()}")
                    print(f"DEBUG: 超出范围的记录数: {((received_values < 1) | (received_values > 300)).sum()}")
                    # 显示几条具体记录
                    print(f"DEBUG: 前5条记录的未来泌乳天数:")
                    for i in range(min(5, len(results_df))):
                        row = results_df.iloc[i]
                        future_days = row.get('未来泌乳天数(天)', 'N/A')
                        mgmt_id = row.get('management_id', 'N/A')
                        print(f"  管理号{mgmt_id}: {future_days}天")
            print(f"DEBUG: =========================")
            
            print(f"筛选成功，结果行数: {len(results_df)}")  # 调试信息
            self.current_results = results_df
            
            # 获取启用的性状列表用于动态创建统计选项卡
            enabled_traits = self._get_enabled_traits()
            if enabled_traits:
                # 重新创建统计选项卡
                self.create_statistics_tabs(enabled_traits)
            
            # 强制刷新界面显示
            self.refresh_results_display(results_df)
            
            self.export_btn.setEnabled(True)

            # 显示统计信息
            self.show_statistics(results_df)
            
            # 更新筛选分析
            if stats:
                print(f"统计信息: {stats}")  # 调试信息
                self.update_analysis_panel(stats)
                
                # 处理尿素氮追踪结果
                if 'urea_tracking' in stats:
                    self.urea_tracking_results = stats['urea_tracking']
                    # 在结果标签页中添加尿素氮追踪标签
                    self.add_urea_tracking_tab()
            else:
                print("没有收到统计信息")  # 调试信息
            
        else:
            print(f"筛选失败: {message}")  # 调试信息
            QMessageBox.critical(self, "筛选失败", message)
        
        self.statusBar().showMessage(message)
    
    def refresh_results_display(self, df):
        """强制刷新结果显示"""
        try:
            # 清空当前表格
            self.result_table.clear()
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            
            # 强制处理待处理的事件
            QApplication.processEvents()
            
            # 重新显示结果
            self.display_results(df)
            
            # 再次强制处理事件，确保界面更新
            QApplication.processEvents()
            
            # 强制重绘表格
            self.result_table.viewport().update()
            self.result_table.update()
            
            print(f"DEBUG: 界面刷新完成，表格当前行数: {self.result_table.rowCount()}")
            
        except Exception as e:
            print(f"DEBUG: 刷新界面时出错: {e}")
            # 如果强制刷新失败，仍然尝试普通显示
            self.display_results(df)
    
    def update_analysis_panel(self, stats):
        """更新筛选分析面板"""
        # 更新各个统计卡片的数值
        getattr(self.total_data_card, 'value_label').setText(str(stats.get('total_cows', 0)))
        getattr(self.range_data_card, 'value_label').setText(str(stats.get('range_cows', 0)))
        getattr(self.result_data_card, 'value_label').setText(str(stats.get('result_cows', 0)))
        getattr(self.rate_data_card, 'value_label').setText(f"{stats.get('filter_rate', 0):.1f}%")
        
        # 切换到筛选分析标签页
        self.tab_widget.setCurrentIndex(2)  # 筛选分析是第3个标签页（索引为2）
    
    def display_results(self, df):
        """显示筛选结果"""
        if df.empty:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return
        
        # 首先过滤掉所有数据都为空的行
        # 检查每行是否至少有一个非空的关键字段
        key_fields = ['management_id', 'parity']
        valid_rows = []
        
        for i, row in df.iterrows():
            # 检查关键字段是否至少有一个不为空
            has_key_data = any(pd.notna(row.get(field)) and str(row.get(field)).strip() != '' for field in key_fields)
            if has_key_data:
                valid_rows.append(i)
        
        # 只显示有效行
        if valid_rows:
            filtered_df = df.loc[valid_rows].copy()
        else:
            # 如果没有有效行，显示空表格
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return
        
        print(f"DEBUG: 原始数据行数: {len(df)}, 有效数据行数: {len(filtered_df)}")
        
        # 列名中英文映射
        column_mapping = {
            'management_id': '管理号',
            'parity': '最后一次取样时的胎次',
            '平均蛋白率(%)': '平均蛋白率(%)',
            '最后一个月泌乳天数(天)': '最后一个月泌乳天数(天)',
            '未来泌乳天数(天)': '未来泌乳天数(天)'
        }
        
        # 获取中文列名
        chinese_columns = []
        for col in filtered_df.columns:
            if col in column_mapping:
                chinese_columns.append(column_mapping[col])
            else:
                chinese_columns.append(col)  # 月份列名已经是中文格式
        
        # 获取总平均值和月度平均值
        overall_avg = getattr(filtered_df, 'attrs', {}).get('overall_protein_avg', None)
        monthly_averages = getattr(filtered_df, 'attrs', {}).get('monthly_averages', {})
        parity_avg = getattr(filtered_df, 'attrs', {}).get('parity_avg', None)
        
        # 设置表格行数（总平均值行 + 月度平均值行 + 有效数据行）
        extra_rows = 0
        if overall_avg is not None:
            extra_rows += 1
        if monthly_averages:
            extra_rows += 1
            
        self.result_table.setRowCount(len(filtered_df) + extra_rows)
        self.result_table.setColumnCount(len(filtered_df.columns))
        self.result_table.setHorizontalHeaderLabels(chinese_columns)
        
        # 添加汇总行
        row_offset = 0
        
        # 第一行：总平均值
        if overall_avg is not None:
            # 不使用合并单元格，在每列设置适当的内容
            for j in range(len(filtered_df.columns)):
                if j == 0:
                    avg_item = QTableWidgetItem(f"所有月份蛋白率总平均值: {overall_avg}%")
                    avg_item.setFont(QFont("微软雅黑", 10, QFont.Weight.Bold))
                else:
                    avg_item = QTableWidgetItem("")
                    
                avg_item.setBackground(QColor(255, 235, 59))  # 黄色背景突出显示
                self.result_table.setItem(row_offset, j, avg_item)
            
            row_offset += 1
        
        # 第二行：各月平均值
        if monthly_averages:
            for j, column_name in enumerate(chinese_columns):
                original_col = filtered_df.columns[j]
                
                if original_col in monthly_averages and monthly_averages[original_col] is not None:
                    # 显示该月的平均值
                    avg_value = monthly_averages[original_col]
                    if '蛋白率' in column_name:
                        # 蛋白率显示百分号
                        month_avg_item = QTableWidgetItem(f"{avg_value}%")
                        month_avg_item.setBackground(QColor(255, 248, 220))  # 浅黄色背景
                    elif '泌乳天数' in column_name:
                        # 泌乳天数显示天数
                        month_avg_item = QTableWidgetItem(f"{avg_value}天")
                        month_avg_item.setBackground(QColor(240, 248, 255))  # 浅蓝色背景
                    elif '产奶量' in column_name:
                        # 产奶量显示单位
                        month_avg_item = QTableWidgetItem(f"{avg_value}Kg")
                        month_avg_item.setBackground(QColor(240, 255, 240))  # 浅绿色背景
                    else:
                        month_avg_item = QTableWidgetItem(str(avg_value))
                        month_avg_item.setBackground(QColor(255, 248, 220))
                    
                    month_avg_item.setFont(QFont("微软雅黑", 9, QFont.Weight.Bold))
                    month_avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif '蛋白率' in column_name:
                    # 蛋白率列但没有数据
                    month_avg_item = QTableWidgetItem("--")
                    month_avg_item.setBackground(QColor(255, 248, 220))
                    month_avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif '泌乳天数' in column_name:
                    # 泌乳天数列但没有数据
                    month_avg_item = QTableWidgetItem("--")
                    month_avg_item.setBackground(QColor(240, 248, 255))
                    month_avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif column_name == '最后一次取样时的胎次' and parity_avg is not None:
                    # 胎次列显示平均胎次
                    month_avg_item = QTableWidgetItem(f"{parity_avg}胎")
                    month_avg_item.setBackground(QColor(240, 255, 240))  # 浅绿色背景
                    month_avg_item.setFont(QFont("微软雅黑", 9, QFont.Weight.Bold))
                    month_avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif j == 0:
                    # 第一列显示标签
                    month_avg_item = QTableWidgetItem("当月平均值")
                    month_avg_item.setBackground(QColor(240, 240, 240))
                    month_avg_item.setFont(QFont("微软雅黑", 9, QFont.Weight.Bold))
                else:
                    # 其他列为空
                    month_avg_item = QTableWidgetItem("")
                    month_avg_item.setBackground(QColor(248, 248, 248))
                
                self.result_table.setItem(row_offset, j, month_avg_item)
            
            row_offset += 1
        
        # 填充有效数据（不再使用原始索引，而是连续填充）
        display_row = row_offset
        for _, row in filtered_df.iterrows():
            for j, value in enumerate(row):
                if pd.notna(value):
                    item = QTableWidgetItem(str(value))
                else:
                    item = QTableWidgetItem("")
                
                # 判断是否为蛋白率相关列，设置黄色背景
                column_name = chinese_columns[j]
                is_protein_column = (
                    '蛋白率' in column_name or 
                    column_name == '平均蛋白率(%)'
                )
                is_lactation_column = (
                    '泌乳天数' in column_name
                )
                is_milk_column = (
                    '产奶量' in column_name
                )
                
                if is_protein_column:
                    # 蛋白率相关列标黄
                    item.setBackground(QColor(255, 248, 220))  # 浅黄色背景
                    if column_name == '平均蛋白率(%)' and pd.notna(value):
                        item.setFont(QFont("微软雅黑", 9, QFont.Weight.Bold))
                elif is_lactation_column:
                    # 泌乳天数相关列标蓝
                    item.setBackground(QColor(240, 248, 255))  # 浅蓝色背景
                elif is_milk_column:
                    # 产奶量相关列标绿
                    item.setBackground(QColor(240, 255, 240))  # 浅绿色背景
                
                self.result_table.setItem(display_row, j, item)
            
            display_row += 1
        
        # 设置表头样式 - 为蛋白率列设置黄色背景
        protein_columns = []
        for j, column_name in enumerate(chinese_columns):
            is_protein_column = (
                '蛋白率' in column_name or 
                column_name == '平均蛋白率(%)'
            )
            if is_protein_column:
                protein_columns.append(j)
        
        # 收集泌乳天数列索引
        lactation_columns = []
        for j, column_name in enumerate(chinese_columns):
            is_lactation_column = '泌乳天数' in column_name
            if is_lactation_column:
                lactation_columns.append(j)
        
        # 收集产奶量列索引
        milk_columns = []
        for j, column_name in enumerate(chinese_columns):
            is_milk_column = '产奶量' in column_name
            if is_milk_column:
                milk_columns.append(j)
        
        # 为特殊列设置样式
        if protein_columns or lactation_columns or milk_columns:
            header_style = """
                QHeaderView::section {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 4px;
                    font-weight: bold;
                }
            """
            
            # 为蛋白率列添加黄色背景的样式
            for col_index in protein_columns:
                header_style += f"""
                    QHeaderView::section:nth-child({col_index + 1}) {{
                        background-color: #fff3cd;
                        color: #856404;
                        font-weight: bold;
                    }}
                """
            
            # 为泌乳天数列添加蓝色背景的样式
            for col_index in lactation_columns:
                header_style += f"""
                    QHeaderView::section:nth-child({col_index + 1}) {{
                        background-color: #e3f2fd;
                        color: #0d47a1;
                        font-weight: bold;
                    }}
                """
            
            # 为产奶量列添加绿色背景的样式
            for col_index in milk_columns:
                header_style += f"""
                    QHeaderView::section:nth-child({col_index + 1}) {{
                        background-color: #d3f5d3;
                        color: #155724;
                        font-weight: bold;
                    }}
                """
            
            self.result_table.horizontalHeader().setStyleSheet(header_style)
        
        # 调整列宽
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.resizeColumnsToContents()
        
        # 切换到结果标签页
        self.tab_widget.setCurrentIndex(1)
        
        print(f"DEBUG: 最终显示行数: {self.result_table.rowCount()}, 列数: {self.result_table.columnCount()}")
    
    def show_statistics(self, df):
        """显示统计信息到不同的选项卡"""
        if df.empty:
            empty_message = "暂无筛选结果\n请检查筛选条件是否过于严格。"
            self.overall_stats_widget.setText(f"📊 总体统计信息\n\n{empty_message}")
            
            # 更新胎次分析
            if hasattr(self, 'parity_stats_widget'):
                self.parity_stats_widget.setText(f"🐄 胎次分析\n\n{empty_message}")
            
            # 更新动态性状选项卡
            if hasattr(self, 'trait_stats_widgets'):
                for trait, widget in self.trait_stats_widgets.items():
                    widget.setText(f"性状分析\n\n{empty_message}")
            
            # 兼容旧版本的固定选项卡
            if hasattr(self, 'protein_stats_widget'):
                self.protein_stats_widget.setText(f"🥛 蛋白率分析\n\n{empty_message}")
            if hasattr(self, 'somatic_stats_widget'):
                self.somatic_stats_widget.setText(f"🔬 体细胞数分析\n\n{empty_message}")
            if hasattr(self, 'other_traits_stats_widget'):
                self.other_traits_stats_widget.setText(f"📈 其他性状分析\n\n{empty_message}")
            return
        
        # 1. 总体统计
        self.update_overall_statistics(df)
        
        # 2. 胎次分析
        self.update_parity_statistics(df)
        
        # 3. 动态性状分析
        if hasattr(self, 'trait_stats_widgets'):
            for trait, widget in self.trait_stats_widgets.items():
                self.update_trait_statistics(df, trait, widget)
        else:
            # 兼容旧版本 - 蛋白率分析
            if hasattr(self, 'protein_stats_widget'):
                self.update_protein_statistics(df)
        
        # 3. 体细胞数分析
        self.update_somatic_statistics(df)
        
        # 4. 胎次分析
        self.update_parity_statistics(df)
        
        # 5. 其他性状分析
        self.update_other_traits_statistics(df)
    
    def update_overall_statistics(self, df):
        """更新总体统计信息"""
        stats = "📊 总体统计信息\n\n"
        
        # 显示总平均蛋白率（来自DataFrame属性）
        overall_avg = getattr(df, 'attrs', {}).get('overall_protein_avg', None)
        if overall_avg is not None:
            stats += f"🎯 所有月份蛋白率总平均值: {overall_avg}%\n"
        
        # 显示平均胎次（来自DataFrame属性）
        parity_avg = getattr(df, 'attrs', {}).get('parity_avg', None)
        if parity_avg is not None:
            stats += f"🐄 群体平均胎次: {parity_avg}胎\n\n"
        else:
            stats += "\n"
        
        stats += f"📊 总记录数: {len(df)}\n"
        
        # 统计唯一牛只数（基于management_id）
        if 'management_id' in df.columns:
            unique_cows = df['management_id'].dropna().nunique()
            stats += f"🐄 符合条件牛只数: {unique_cows}头\n"
        
        # 最后一个月泌乳天数统计
        if '最后一个月泌乳天数' in df.columns:
            lactation_data = df['最后一个月泌乳天数'].dropna()
            if not lactation_data.empty:
                stats += f"\n⏰ 最后一个月泌乳天数:\n"
                stats += f"  平均: {lactation_data.mean():.1f}天\n"
                stats += f"  范围: {lactation_data.min():.0f}-{lactation_data.max():.0f}天\n"
        
        self.overall_stats_widget.setText(stats)
    
    def update_protein_statistics(self, df):
        """更新蛋白率分析信息"""
        stats = "🥛 蛋白率分析\n\n"
        
        # 个体平均蛋白率统计
        if '平均蛋白率(%)' in df.columns:
            individual_avg = df['平均蛋白率(%)'].dropna()
            if not individual_avg.empty:
                stats += f"📈 个体平均蛋白率分布:\n"
                stats += f"  最低个体平均值: {individual_avg.min():.2f}%\n"
                stats += f"  最高个体平均值: {individual_avg.max():.2f}%\n"
                stats += f"  群体平均值: {individual_avg.mean():.2f}%\n"
                stats += f"  标准差: {individual_avg.std():.2f}%\n\n"
        
        # 蛋白率详细统计（仅当有蛋白率数据时显示）
        protein_columns = [col for col in df.columns if col.endswith('月蛋白率(%)')]
        if protein_columns:
            stats += f"📅 蛋白率月度明细:\n"
            # 按时间顺序排列月份列
            sorted_protein_cols = sorted(protein_columns, key=lambda x: x[:7])  # 按YYYY年MM月排序
            
            for col in sorted_protein_cols:
                protein_data = df[col].dropna()
                if not protein_data.empty:
                    month_name = col.replace('蛋白率(%)', '')
                    stats += f"  {month_name}:\n"
                    stats += f"    平均: {protein_data.mean():.2f}%\n"
                    stats += f"    范围: {protein_data.min():.2f}%-{protein_data.max():.2f}%\n"
                    stats += f"    标准差: {protein_data.std():.2f}%\n"
                    stats += f"    样本数: {len(protein_data)}头\n\n"
        else:
            stats += f"📅 当前筛选结果中无蛋白率数据\n\n"
        
        # 总体平均蛋白率（来自DataFrame属性，仅当有蛋白率数据时显示）
        overall_avg = getattr(df, 'attrs', {}).get('overall_protein_avg', None)
        if overall_avg is not None:
            stats += f"💡 计算说明:\n"
            stats += f"  • 所有月份蛋白率总平均值: {overall_avg}%\n"
            stats += f"  • 采用产奶量加权平均计算\n"
            stats += f"  • 个体平均值采用算术平均\n"
        elif protein_columns:  # 有蛋白率列但没有总平均值
            stats += f"💡 计算说明:\n"
            stats += f"  • 无法计算总平均值（缺少产奶量数据）\n"
            stats += f"  • 个体平均值采用算术平均\n"
        
        self.protein_stats_widget.setText(stats)
    
    def update_somatic_statistics(self, df):
        """更新体细胞数分析信息"""
        stats = "🔬 体细胞数分析\n\n"
        
        # 体细胞数详细统计
        somatic_columns = [col for col in df.columns if '体细胞数' in col and col.endswith('万/ml)')]
        if somatic_columns:
            stats += f"📅 体细胞数月度明细:\n"
            # 按时间顺序排列月份列
            sorted_somatic_cols = sorted(somatic_columns, key=lambda x: x[:7])  # 按YYYY年MM月排序
            
            for col in sorted_somatic_cols:
                somatic_data = df[col].dropna()
                if not somatic_data.empty:
                    month_name = col.replace('体细胞数(万/ml)', '')
                    stats += f"  {month_name}:\n"
                    stats += f"    平均: {somatic_data.mean():.1f}万/ml\n"
                    stats += f"    范围: {somatic_data.min():.1f}-{somatic_data.max():.1f}万/ml\n"
                    stats += f"    标准差: {somatic_data.std():.1f}万/ml\n"
                    stats += f"    样本数: {len(somatic_data)}头\n\n"
        
        if not somatic_columns:
            stats += "本次筛选结果中无体细胞数数据。\n\n"
        
        stats += f"💡 说明:\n"
        stats += f"  • 体细胞数以万/ml为单位\n"
        stats += f"  • 数值越低表示乳房健康状况越好\n"
        stats += f"  • 正常范围通常在10-40万/ml之间\n"
        
        self.somatic_stats_widget.setText(stats)
    
    def update_parity_statistics(self, df):
        """更新胎次分析信息"""
        stats = "🐄 胎次分析\n\n"
        
        # 按胎次统计  
        if 'parity' in df.columns:
            parity_counts = df['parity'].value_counts().sort_index()
            stats += f"📊 各胎次分布:\n"
            total_cows = parity_counts.sum()
            for parity, count in parity_counts.items():
                percentage = (count / total_cows) * 100
                stats += f"  {parity}胎: {count}头 ({percentage:.1f}%)\n"
            
            # 胎次统计指标
            parity_data = df['parity'].dropna()
            if not parity_data.empty:
                stats += f"\n📈 胎次统计指标:\n"
                stats += f"  平均胎次: {parity_data.mean():.1f}胎\n"
                stats += f"  胎次范围: {parity_data.min():.0f}-{parity_data.max():.0f}胎\n"
                stats += f"  中位数胎次: {parity_data.median():.0f}胎\n"
                stats += f"  总牛头数: {len(parity_data)}头\n"
                
                # 胎次分组分析
                stats += f"\n🔍 胎次分组分析:\n"
                first_parity = parity_counts.get(1, 0)
                second_parity = parity_counts.get(2, 0)
                third_plus = parity_counts[parity_counts.index >= 3].sum() if len(parity_counts[parity_counts.index >= 3]) > 0 else 0
                
                stats += f"  头胎牛: {first_parity}头 ({(first_parity/total_cows)*100:.1f}%)\n"
                stats += f"  二胎牛: {second_parity}头 ({(second_parity/total_cows)*100:.1f}%)\n"
                stats += f"  三胎及以上: {third_plus}头 ({(third_plus/total_cows)*100:.1f}%)\n"
        
        self.parity_stats_widget.setText(stats)
    
    def update_other_traits_statistics(self, df):
        """更新其他性状分析信息"""
        stats = "📈 其他性状分析\n\n"
        
        # 产奶量详细统计
        milk_columns = [col for col in df.columns if col.endswith('月产奶量(Kg)')]
        if milk_columns:
            stats += f"🥛 产奶量月度明细:\n"
            # 按时间顺序排列月份列
            sorted_milk_cols = sorted(milk_columns, key=lambda x: x[:7])  # 按YYYY年MM月排序
            
            for col in sorted_milk_cols:
                milk_data = df[col].dropna()
                if not milk_data.empty:
                    month_name = col.replace('产奶量(Kg)', '')
                    stats += f"  {month_name}:\n"
                    stats += f"    平均: {milk_data.mean():.1f}Kg\n"
                    stats += f"    范围: {milk_data.min():.1f}-{milk_data.max():.1f}Kg\n"
                    stats += f"    标准差: {milk_data.std():.1f}Kg\n"
                    stats += f"    样本数: {len(milk_data)}头\n\n"
        
        # 其他性状统计（乳脂率、泌乳天数等）
        other_trait_patterns = [
            ('乳脂率', '月乳脂率(%)', '%'),
            ('泌乳天数', '月泌乳天数(天)', '天'),
            ('乳糖率', '月乳糖率(%)', '%'),
            ('固形物', '月固形物(%)', '%'),
            ('脂蛋比', '月脂蛋比', ''),
            ('尿素氮', '月尿素氮(mg/dl)', 'mg/dl')
        ]
        
        for trait_name, pattern, unit in other_trait_patterns:
            trait_columns = [col for col in df.columns if pattern in col]
            if trait_columns:
                stats += f"📊 {trait_name}分析:\n"
                # 按时间顺序排列
                sorted_cols = sorted(trait_columns, key=lambda x: x[:7])
                
                for col in sorted_cols:
                    trait_data = df[col].dropna()
                    if not trait_data.empty:
                        month_name = col.replace(pattern, '')
                        stats += f"  {month_name}: 平均 {trait_data.mean():.2f}{unit} "
                        stats += f"(范围: {trait_data.min():.2f}-{trait_data.max():.2f}{unit})\n"
                stats += "\n"
        
        if not milk_columns and not any(df.columns.str.contains(pattern).any() for _, pattern, _ in other_trait_patterns):
            stats += "本次筛选结果中暂无其他性状数据。\n"
        
        self.other_traits_stats_widget.setText(stats)
    
    def export_results(self):
        """导出结果"""
        if self.current_results.empty:
            self.show_warning("警告", "没有可导出的结果")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存筛选结果",
            f"DHI筛选结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel文件 (*.xlsx)"
        )
        
        if filename:
            try:
                self._export_formatted_excel(filename)
                
                # 使用美观的自定义对话框
                self.show_export_success_dialog("DHI筛选结果已保存到：", filename)
                
                self.statusBar().showMessage(f"已导出到: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败:\n{str(e)}")

    def open_file(self, file_path):
        """打开文件"""
        try:
            import subprocess
            import os
            
            if os.path.exists(file_path):
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # macOS and Linux
                    if sys.platform == 'darwin':  # macOS
                        subprocess.run(['open', file_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', file_path])
                
                print(f"正在打开文件: {file_path}")
            else:
                QMessageBox.warning(self, "错误", f"文件不存在:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开文件:\n{str(e)}")

    def open_file_folder(self, file_path):
        """打开文件所在文件夹"""
        try:
            import subprocess
            import os
            
            if os.path.exists(file_path):
                folder_path = os.path.dirname(file_path)
                
                if os.name == 'nt':  # Windows
                    # 在Windows中打开文件夹并选中文件
                    subprocess.run(['explorer', '/select,', file_path])
                elif os.name == 'posix':  # macOS and Linux
                    if sys.platform == 'darwin':  # macOS
                        # 在macOS中打开Finder并选中文件
                        subprocess.run(['open', '-R', file_path])
                    else:  # Linux
                        # 在Linux中打开文件管理器
                        subprocess.run(['xdg-open', folder_path])
                
                print(f"正在打开文件夹: {folder_path}")
            else:
                QMessageBox.warning(self, "错误", f"文件不存在:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开文件夹:\n{str(e)}")
    
    def _export_formatted_excel(self, filename):
        """导出格式化的Excel文件"""
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        # 创建工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "筛选结果"
        
        df = self.current_results
        
        # 列名中英文映射（与界面显示一致）
        column_mapping = {
            'management_id': '管理号',
            'parity': '最后一次取样时的胎次',
            '平均蛋白率(%)': '平均蛋白率(%)',
            '最后一个月泌乳天数(天)': '最后一个月泌乳天数(天)',
            '未来泌乳天数(天)': '未来泌乳天数(天)'
        }
        
        # 获取中文列名
        chinese_columns = []
        for col in df.columns:
            if col in column_mapping:
                chinese_columns.append(column_mapping[col])
            else:
                chinese_columns.append(col)  # 月份列名已经是中文格式
        
        # 获取总平均值和月度平均值
        overall_avg = getattr(df, 'attrs', {}).get('overall_protein_avg', None)
        monthly_averages = getattr(df, 'attrs', {}).get('monthly_averages', {})
        parity_avg = getattr(df, 'attrs', {}).get('parity_avg', None)
        
        # 样式定义
        yellow_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")  # 浅黄色
        dark_yellow_fill = PatternFill(start_color="FFEB3B", end_color="FFEB3B", fill_type="solid")  # 深黄色
        gray_fill = PatternFill(start_color="F8F8F8", end_color="F8F8F8", fill_type="solid")  # 灰色
        light_gray_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")  # 浅灰色
        
        header_font = Font(bold=True, size=11)
        bold_font = Font(bold=True, size=10)
        normal_font = Font(size=10)
        
        center_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        # 当前行位置
        current_row = 1
        
        # 1. 写入总平均值行
        if overall_avg is not None:
            # 不使用合并单元格，直接在第一列显示总平均值
            for j in range(1, len(chinese_columns) + 1):
                cell = ws.cell(row=current_row, column=j)
                if j == 1:
                    cell.value = f"所有月份蛋白率总平均值: {overall_avg}%"
                    cell.font = header_font
                else:
                    cell.value = ""
                    cell.font = normal_font
                cell.fill = dark_yellow_fill
                cell.alignment = center_alignment
                cell.border = thin_border
            current_row += 1
        
        # 2. 写入各月平均值行
        if monthly_averages:
            # 定义浅蓝色填充（用于泌乳天数）
            light_blue_fill = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
            # 定义浅绿色填充（用于胎次）
            light_green_fill = PatternFill(start_color="E8F5E8", end_color="E8F5E8", fill_type="solid")
            
            for j, column_name in enumerate(chinese_columns, 1):
                original_col = df.columns[j-1]
                cell = ws.cell(row=current_row, column=j)
                
                if original_col in monthly_averages and monthly_averages[original_col] is not None:
                    # 显示该月的平均值
                    avg_value = monthly_averages[original_col]
                    if '蛋白率' in column_name:
                        # 蛋白率显示百分号
                        cell.value = f"{avg_value}%"
                        cell.fill = yellow_fill
                    elif '泌乳天数' in column_name:
                        # 泌乳天数显示天数
                        cell.value = f"{avg_value}天"
                        cell.fill = light_blue_fill
                    elif '产奶量' in column_name:
                        # 产奶量显示单位
                        cell.value = f"{avg_value}Kg"
                        cell.fill = light_green_fill
                    else:
                        cell.value = str(avg_value)
                        cell.fill = yellow_fill
                    
                    cell.font = bold_font
                    cell.alignment = center_alignment
                elif '蛋白率' in column_name:
                    # 蛋白率列但没有数据
                    cell.value = "--"
                    cell.fill = yellow_fill
                    cell.alignment = center_alignment
                elif '泌乳天数' in column_name:
                    # 泌乳天数列但没有数据
                    cell.value = "--"
                    cell.fill = light_blue_fill
                    cell.alignment = center_alignment
                elif column_name == '最后一次取样时的胎次' and parity_avg is not None:
                    # 胎次列显示平均胎次
                    cell.value = f"{parity_avg}胎"
                    cell.fill = light_green_fill
                    cell.font = bold_font
                    cell.alignment = center_alignment
                elif j == 1:
                    # 第一列显示标签
                    cell.value = "当月平均值"
                    cell.fill = light_gray_fill
                    cell.font = bold_font
                else:
                    # 其他列为空
                    cell.value = ""
                    cell.fill = gray_fill
                
                cell.border = thin_border
            
            current_row += 1
        
        # 3. 写入表头
        for j, column_name in enumerate(chinese_columns, 1):
            cell = ws.cell(row=current_row, column=j, value=column_name)
            cell.font = header_font
            cell.alignment = center_alignment
            cell.border = thin_border
            
            # 蛋白率相关列标黄
            is_protein_column = ('蛋白率' in column_name or column_name == '平均蛋白率(%)')
            is_milk_column = '产奶量' in column_name
            if is_protein_column:
                cell.fill = yellow_fill
            elif is_milk_column:
                cell.fill = light_green_fill
        
        current_row += 1
        
        # 4. 写入数据
        for _, row in df.iterrows():
            for j, value in enumerate(row, 1):
                cell = ws.cell(row=current_row, column=j)
                
                # 特殊处理泌乳天数列，确保显示为整数
                column_name = chinese_columns[j-1]
                if '泌乳天数' in column_name and pd.notna(value):
                    try:
                        cell.value = int(float(value))
                    except (ValueError, TypeError):
                        cell.value = value if pd.notna(value) else ""
                else:
                    cell.value = value if pd.notna(value) else ""
                
                cell.font = normal_font
                cell.border = thin_border
                cell.alignment = center_alignment
                
                # 根据列类型设置背景色
                is_protein_column = ('蛋白率' in column_name or column_name == '平均蛋白率(%)')
                is_lactation_column = '泌乳天数' in column_name
                is_milk_column = '产奶量' in column_name
                
                if is_protein_column:
                    cell.fill = yellow_fill
                    if column_name == '平均蛋白率(%)' and pd.notna(value):
                        cell.font = bold_font
                elif is_lactation_column:
                    cell.fill = light_blue_fill
                elif is_milk_column:
                    cell.fill = light_green_fill
            
            current_row += 1
        
        # 5. 调整列宽
        for col_num in range(1, len(chinese_columns) + 1):
            max_length = 0
            column_letter = ws.cell(row=1, column=col_num).column_letter
            
            # 遍历该列的所有单元格（跳过合并单元格）
            for row_num in range(1, current_row):
                try:
                    cell = ws.cell(row=row_num, column=col_num)
                    # 跳过合并单元格
                    if hasattr(cell, 'value') and cell.value is not None:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except:
                    pass
            
            # 设置列宽，考虑中文字符
            adjusted_width = min(max(max_length * 1.2, 10), 25)  # 中文字符需要更多空间
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # 保存文件
        wb.save(filename)

    def create_special_filter_group(self, title: str, filter_type: str):
        """创建特殊筛选组（蛋白率、体细胞数等）
        
        Args:
            title: 组标题
            filter_type: 筛选类型 ('protein' 或 'somatic')
        """
        group = self.create_card_widget(title)
        layout = QVBoxLayout(group.content_widget)
        
        # 自适应边距
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        scale_factor = self.display_scale / 100.0
        margin = max(int(15 * dpi_ratio * scale_factor), 8)
        
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # 获取样式
        form_styles = self.get_responsive_form_styles()
        checkbox_font_size = max(int(13 * dpi_ratio * 0.7), 12)
        checkbox_spacing = max(int(8 * dpi_ratio * 0.6), 6)
        checkbox_size = max(int(16 * dpi_ratio * 0.6), 14)
        checkbox_border_radius = max(int(3 * dpi_ratio * 0.6), 2)
        dash_font_size = max(int(14 * dpi_ratio), 12)
        dash_margin = max(int(8 * dpi_ratio), 6)
        
        # 启用开关
        filter_enabled = QCheckBox(f"启用{title}")
        filter_enabled.setChecked(False)
        filter_enabled.setToolTip(f"勾选后启用{title}筛选")
        filter_enabled.setStyleSheet(f"""
            QCheckBox {{
                font-size: {checkbox_font_size}px;
                color: #495057;
                spacing: {checkbox_spacing}px;
                font-weight: bold;
            }}
            QCheckBox::indicator {{
                width: {checkbox_size}px;
                height: {checkbox_size}px;
                border: 2px solid #ced4da;
                border-radius: {checkbox_border_radius}px;
                background-color: white;
            }}
            QCheckBox::indicator:hover {{
                border-color: #80bdff;
                background-color: #f8f9fa;
            }}
            QCheckBox::indicator:checked {{
                background-color: #28a745 !important;
                border-color: #28a745 !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: #218838 !important;
                border-color: #218838 !important;
            }}
            QCheckBox::indicator:checked:pressed {{
                background-color: #1e7e34 !important;
                border-color: #1e7e34 !important;
            }}
        """)
        layout.addWidget(filter_enabled)
        
        # 筛选范围
        range_layout = QHBoxLayout()
        range_min = QDoubleSpinBox()
        range_max = QDoubleSpinBox()
        
        if filter_type == "protein":
            range_min.setRange(0.0, 999999.99)
            range_min.setSingleStep(0.01)
            range_min.setDecimals(2)
            range_max.setRange(0.0, 999999.99)
            range_max.setSingleStep(0.01)
            range_max.setDecimals(2)
            
            # 使用实际数据范围
            if hasattr(self, 'current_data_ranges') and 'protein_pct' in self.current_data_ranges:
                field_range = self.current_data_ranges['protein_pct']
                actual_min = field_range['min']
                actual_max = field_range['max']
                range_min.setValue(actual_min)
                range_max.setValue(actual_max)
                print(f"蛋白率筛选实际数据范围: {actual_min}-{actual_max}%")
            else:
                range_min.setValue(3.00)
                range_max.setValue(4.50)
            
            range_label = QLabel("蛋白率范围(%):")
        elif filter_type == "somatic":
            range_min.setRange(0.0, 999999.99)
            range_min.setSingleStep(0.1)
            range_min.setDecimals(1)
            range_max.setRange(0.0, 999999.99)
            range_max.setSingleStep(0.1)
            range_max.setDecimals(1)
            
            # 使用实际数据范围
            if hasattr(self, 'current_data_ranges') and 'somatic_cell_count' in self.current_data_ranges:
                field_range = self.current_data_ranges['somatic_cell_count']
                actual_min = field_range['min']
                actual_max = field_range['max']
                range_min.setValue(actual_min)
                range_max.setValue(actual_max)
                print(f"体细胞数筛选实际数据范围: {actual_min}-{actual_max}万/ml")
            else:
                range_min.setValue(0.0)
                range_max.setValue(50.0)
            
            range_label = QLabel("体细胞数范围(万/ml):")
        
        range_min.setStyleSheet(form_styles)
        range_max.setStyleSheet(form_styles)
        range_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        range_layout.addWidget(range_label)
        range_layout.addWidget(range_min)
        dash_label = QLabel("—")
        dash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_label.setStyleSheet(f"color: #6c757d; margin: 0 {dash_margin}px; font-size: {dash_font_size}px;")
        range_layout.addWidget(dash_label)
        range_layout.addWidget(range_max)
        range_layout.addStretch()
        
        range_widget = QWidget()
        range_widget.setLayout(range_layout)
        layout.addWidget(range_widget)
        
        # 最少符合月数
        months_layout = QHBoxLayout()
        months_spinbox = QSpinBox()
        
        # 使用智能月数上限
        max_months = 12  # 默认值
        if hasattr(self, 'current_data_ranges'):
            max_months = self.current_data_ranges.get('months', {}).get('max', 12)
        
        months_spinbox.setRange(0, max_months)
        default_months = min(3, max_months // 2) if max_months > 0 else 1
        months_spinbox.setValue(default_months)
        months_spinbox.setStyleSheet(form_styles)
        months_label = QLabel(f"{title}最少符合月数 (0-{max_months}):")
        months_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        months_layout.addWidget(months_label)
        months_layout.addWidget(months_spinbox)
        months_layout.addStretch()
        
        months_widget = QWidget()
        months_widget.setLayout(months_layout)
        layout.addWidget(months_widget)
        
        # 空值处理策略选择
        empty_layout = QHBoxLayout()
        empty_label = QLabel(f"{title}空值处理策略:")
        empty_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        empty_combo = QComboBox()
        empty_combo.addItems(["视为不符合", "视为符合", "历史数据填充"])
        empty_combo.setCurrentText("视为不符合")  # 默认选择
        empty_combo.setStyleSheet(form_styles)
        empty_combo.setToolTip(f"选择{title}数据为空时的处理方式")
        
        empty_layout.addWidget(empty_label)
        empty_layout.addWidget(empty_combo)
        empty_layout.addStretch()
        
        empty_widget = QWidget()
        empty_widget.setLayout(empty_layout)
        layout.addWidget(empty_widget)
        
        # 控制组件启用状态
        def toggle_filter_controls():
            enabled = filter_enabled.isChecked()
            range_widget.setEnabled(enabled)
            months_widget.setEnabled(enabled)
            empty_widget.setEnabled(enabled)
        
        filter_enabled.toggled.connect(toggle_filter_controls)
        toggle_filter_controls()  # 初始化状态
        
        # 存储控件引用以便后续访问
        if filter_type == "protein":
            self.protein_enabled = filter_enabled
            self.protein_min = range_min
            self.protein_max = range_max
            self.protein_months = months_spinbox
            self.protein_empty = empty_combo
        elif filter_type == "somatic":
            self.somatic_enabled = filter_enabled
            self.somatic_min = range_min
            self.somatic_max = range_max
            self.somatic_months = months_spinbox
            self.somatic_empty = empty_combo
        
        return group
    
    def select_active_cattle_file(self):
        """选择在群牛文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择在群牛文件",
            "",
            "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_path:
            filename = os.path.basename(file_path)
            success, message, cattle_list = self.processor.process_active_cattle_file(file_path, filename)
            
            if success:
                cattle_count = len(cattle_list) if cattle_list else 0
                self.active_cattle_label.setText(f"已加载: {filename} ({cattle_count}头牛)")
                self.active_cattle_label.setStyleSheet("color: #28a745; font-size: 12px; font-weight: bold;")
                self.clear_active_cattle_btn.setVisible(True)
                QMessageBox.information(self, "成功", message)
            else:
                QMessageBox.critical(self, "错误", message)
    
    def clear_active_cattle(self):
        """清除在群牛数据"""
        reply = QMessageBox.question(
            self, 
            "确认清除", 
            "确定要清除在群牛数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.processor.clear_active_cattle_data()
            self.active_cattle_label.setText("未上传在群牛文件")
            self.active_cattle_label.setStyleSheet("color: #6c757d; font-size: 12px;")
            self.clear_active_cattle_btn.setVisible(False)
            QMessageBox.information(self, "成功", "已清除在群牛数据")
    
    def on_filter_checkbox_toggled(self, filter_key, checked):
        """当筛选项复选框状态改变时触发"""
        if checked:
            # 添加筛选项
            if filter_key not in self.added_other_filters:
                # 使用新的配置加载方法
                filter_config = self.load_filter_config(filter_key)
                
                filter_widget = self.create_other_filter_widget(filter_key, filter_config)
                self.other_filters_layout.insertWidget(self.other_filters_layout.count() - 1, filter_widget)
                self.added_other_filters[filter_key] = filter_widget
                # 动态调整容器高度
                self.adjust_filters_container_height()
        else:
            # 移除筛选项
            if filter_key in self.added_other_filters:
                widget = self.added_other_filters[filter_key]
                self.other_filters_layout.removeWidget(widget)
                widget.deleteLater()
                del self.added_other_filters[filter_key]
                # 动态调整容器高度
                self.adjust_filters_container_height()
    
    def quick_add_common_filters(self):
        """一键添加常用筛选项"""
        common_filters = ['fat_pct', 'milk_yield', 'lactose_pct', 'solid_pct']  # 常用筛选项
        
        for filter_key in common_filters:
            if filter_key in self.filter_checkboxes:
                checkbox = self.filter_checkboxes[filter_key]
                if not checkbox.isChecked():
                    checkbox.setChecked(True)
    
    def select_all_filters(self):
        """全选所有筛选项"""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(True)
    
    def clear_all_filters(self):
        """清空所有筛选项选择"""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(False)
    
    def apply_selected_filters(self):
        """应用选中的筛选项"""
        selected_count = sum(1 for checkbox in self.filter_checkboxes.values() if checkbox.isChecked())
        
        if selected_count == 0:
            QMessageBox.information(self, "提示", "请先选择要添加的筛选项目")
            return
        
        QMessageBox.information(
            self, 
            "应用成功", 
            f"已应用 {selected_count} 个筛选项目\n\n请在下方配置相应的筛选条件。"
        )
    
    def adjust_filters_container_height(self):
        """根据添加的筛选项数量动态调整容器高度"""
        if not hasattr(self, 'filters_container') or not hasattr(self, 'added_other_filters'):
            return
        
        # 计算所需高度：每个筛选项约120px高度，加上一些边距
        filter_count = len(self.added_other_filters)
        if filter_count == 0:
            # 没有筛选项时，保持最小高度
            min_height = 50
            self.filters_container.setMinimumHeight(min_height)
            self.filters_container.setMaximumHeight(min_height)
        else:
            # 根据筛选项数量计算高度
            item_height = 120  # 每个筛选项的约定高度
            padding = 20       # 上下边距
            total_height = filter_count * item_height + padding
            
            # 只设置最小高度，最大高度不限制，让容器自动扩展
            self.filters_container.setMinimumHeight(total_height)
            self.filters_container.setMaximumHeight(16777215)  # 设置为最大值，不限制高度
        
        # 强制重新布局
        self.filters_container.updateGeometry()
        if hasattr(self, 'filters_container') and self.filters_container.parent():
            self.filters_container.parent().updateGeometry()
    
    def add_other_filter(self, text):
        """添加其他筛选项（保留兼容性）"""
        # 这个方法现在主要用于保持兼容性
        pass
    
    def create_other_filter_widget(self, filter_key: str, filter_config: Dict):
        """创建其他筛选项的界面组件"""
        chinese_name = filter_config.get("chinese_name", filter_key)
        
        # 获取form_styles
        form_styles = self.get_responsive_form_styles()
        
        # 主容器
        widget = QWidget()
        widget.setMinimumWidth(550)  # 增加最小宽度确保内容显示完整
        widget.setMinimumHeight(140)  # 设置最小高度确保足够空间
        widget.setStyleSheet("""
            QWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                margin: 4px;
                background-color: #f8f9fa;
            }
        """)
        layout = QVBoxLayout(widget)
        
        # 标题行（包含删除按钮）
        title_layout = QHBoxLayout()
        
        # 启用复选框
        enabled_checkbox = QCheckBox(f"启用{chinese_name}筛选")
        enabled_checkbox.setChecked(False)
        
        # 获取屏幕DPI信息用于自适应样式
        screen_info = self.get_safe_screen_info()
        dpi_ratio = screen_info['dpi_ratio']
        checkbox_font_size = max(int(13 * dpi_ratio * 0.7), 12)
        checkbox_spacing = max(int(8 * dpi_ratio * 0.6), 6)
        checkbox_size = max(int(16 * dpi_ratio * 0.6), 14)
        checkbox_border_radius = max(int(3 * dpi_ratio * 0.6), 2)
        
        # 设置完整的复选框样式，包含hover状态
        enabled_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: {checkbox_font_size}px;
                color: #495057;
                spacing: {checkbox_spacing}px;
                font-weight: bold;
            }}
            QCheckBox::indicator {{
                width: {checkbox_size}px;
                height: {checkbox_size}px;
                border: 2px solid #ced4da;
                border-radius: {checkbox_border_radius}px;
                background-color: white;
            }}
            QCheckBox::indicator:hover {{
                border-color: #80bdff;
                background-color: #f8f9fa;
            }}
            QCheckBox::indicator:checked {{
                background-color: #28a745 !important;
                border-color: #28a745 !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: #218838 !important;
                border-color: #218838 !important;
            }}
            QCheckBox::indicator:checked:pressed {{
                background-color: #1e7e34 !important;
                border-color: #1e7e34 !important;
            }}
        """)
        
        title_layout.addWidget(enabled_checkbox)
        
        title_layout.addStretch()
        
        # 删除按钮
        remove_btn = QPushButton("❌")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_other_filter(filter_key))
        title_layout.addWidget(remove_btn)
        
        layout.addLayout(title_layout)
        
        # 筛选范围
        range_layout = QHBoxLayout()
        
        range_min = QDoubleSpinBox()
        range_min.setRange(-999999.99, 999999.99)
        range_min.setDecimals(2)
        
        range_max = QDoubleSpinBox()
        range_max.setRange(-999999.99, 999999.99)
        range_max.setDecimals(2)
        
        # 使用实际数据范围 - 如果有数据范围，使用实际的最小值和最大值
        if hasattr(self, 'current_data_ranges') and filter_key in self.current_data_ranges:
            field_range = self.current_data_ranges[filter_key]
            actual_min = field_range['min']
            actual_max = field_range['max']
            range_min.setValue(actual_min)
            range_max.setValue(actual_max)
            print(f"为{chinese_name}设置实际数据范围: {actual_min}-{actual_max}")
        else:
            # 使用配置中的默认值
            range_min.setValue(filter_config.get("min", 0.0))
            range_max.setValue(filter_config.get("max", 100.0))
        
        range_layout.addWidget(QLabel(f"{chinese_name}范围:"))
        range_layout.addWidget(range_min)
        range_layout.addWidget(QLabel("—"))
        range_layout.addWidget(range_max)
        range_layout.addStretch()
        
        layout.addLayout(range_layout)
        
        # 最少符合月数和空值处理
        options_layout = QHBoxLayout()
        
        months_spinbox = QSpinBox()
        # 使用智能月数上限
        max_months = 12  # 默认值
        if hasattr(self, 'current_data_ranges'):
            max_months = self.current_data_ranges.get('months', {}).get('max', 12)
        
        months_spinbox.setRange(0, max_months)
        default_months = min(3, max_months // 2) if max_months > 0 else 1
        months_spinbox.setValue(filter_config.get("min_match_months", default_months))
        
        # 空值处理策略下拉选择
        empty_combo = QComboBox()
        empty_combo.addItems(["视为不符合", "视为符合", "历史数据填充"])
        # 根据配置设置默认值
        if filter_config.get("treat_empty_as_match", False):
            empty_combo.setCurrentText("视为符合")
        else:
            empty_combo.setCurrentText("视为不符合")
        empty_combo.setStyleSheet(form_styles)
        empty_combo.setToolTip("选择数据为空时的处理方式")
        
        options_layout.addWidget(QLabel("最少符合月数:"))
        options_layout.addWidget(months_spinbox)
        options_layout.addWidget(QLabel("空值处理:"))
        options_layout.addWidget(empty_combo)
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        # 控制启用状态
        def toggle_controls():
            enabled = enabled_checkbox.isChecked()
            for i in range(range_layout.count()):
                item = range_layout.itemAt(i)
                if item.widget():
                    item.widget().setEnabled(enabled)
            for i in range(options_layout.count()):
                item = options_layout.itemAt(i)
                if item.widget():
                    item.widget().setEnabled(enabled)
        
        enabled_checkbox.toggled.connect(toggle_controls)
        toggle_controls()
        
        # 存储控件引用
        widget.enabled_checkbox = enabled_checkbox
        widget.range_min = range_min
        widget.range_max = range_max
        widget.months_spinbox = months_spinbox
        widget.empty_combo = empty_combo
        widget.filter_key = filter_key
        widget.chinese_name = chinese_name
        
        return widget
    
    def remove_other_filter(self, filter_key: str):
        """移除其他筛选项"""
        if filter_key in self.added_other_filters:
            widget = self.added_other_filters[filter_key]
            self.other_filters_layout.removeWidget(widget)
            widget.deleteLater()
            del self.added_other_filters[filter_key]
            
            # 同步更新复选框状态
            if filter_key in self.filter_checkboxes:
                checkbox = self.filter_checkboxes[filter_key]
                checkbox.blockSignals(True)  # 阻止信号避免递归调用
                checkbox.setChecked(False)
                checkbox.blockSignals(False)
            
            # 动态调整容器高度
            self.adjust_filters_container_height()
    
    
    def _check_filter_thread_stopped(self):
        """检查筛选线程是否已停止"""
        if hasattr(self, 'filter_thread') and self.filter_thread.isRunning():
            # 线程还在运行，继续等待
            QTimer.singleShot(100, self._check_filter_thread_stopped)
        else:
            # 线程已停止，重置UI状态
            self._reset_filter_ui_state()
            self.statusBar().showMessage("筛选已被用户取消")
    
    def _reset_filter_ui_state(self):
        """重置筛选UI状态"""
        if hasattr(self, 'filter_progress'):
            self.filter_progress.setVisible(False)
        if hasattr(self, 'filter_btn'):
            self.filter_btn.setEnabled(True)
            self.filter_btn.setVisible(True)
        if hasattr(self, 'cancel_filter_btn'):
            self.cancel_filter_btn.setEnabled(False)
            self.cancel_filter_btn.setVisible(False)
    
    def _get_enabled_traits(self):
        """获取当前启用的性状列表"""
        enabled_traits = []
        
        # 检查蛋白率筛选
        if hasattr(self, 'protein_enabled') and self.protein_enabled.isChecked():
            enabled_traits.append('protein_pct')
        
        # 检查体细胞数筛选
        if hasattr(self, 'somatic_enabled') and self.somatic_enabled.isChecked():
            enabled_traits.append('somatic_cell_count')
        
        # 检查其他筛选项
        for filter_key, widget in self.added_other_filters.items():
            if widget.enabled_checkbox.isChecked():
                enabled_traits.append(filter_key)
        
        return enabled_traits
    
    def update_trait_statistics(self, df, trait, widget):
        """更新特定性状的统计信息"""
        if df.empty:
            widget.setText(f"性状分析\n\n暂无筛选结果")
            return
        
        # 性状中文名称映射
        trait_names = {
            'protein_pct': '🥛 蛋白率',
            'somatic_cell_count': '🔬 体细胞数',
            'fat_pct': '🧈 乳脂率',
            'lactose_pct': '🍬 乳糖率',
            'milk_yield': '🥛 产奶量',
            'lactation_days': '📅 泌乳天数',
            'solids_pct': '🧪 固形物',
            'fat_protein_ratio': '⚖️ 脂蛋比',
            'urea_nitrogen': '🧬 尿素氮',
            'total_fat_pct': '🧈 总乳脂',
            'total_protein_pct': '🥛 总蛋白',
            'mature_equivalent': '🐄 成年当量'
        }
        
        trait_name = trait_names.get(trait, trait)
        stats_text = f"{trait_name}分析\n\n"
        
        # 查找对应的月度明细列
        monthly_columns = []
        for col in df.columns:
            if trait == 'protein_pct' and '蛋白率(%)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'somatic_cell_count' and '体细胞数(万/ml)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'fat_pct' and '乳脂率(%)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'lactose_pct' and '乳糖率(%)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'milk_yield' and '产奶量(Kg)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'lactation_days' and '泌乳天数(天)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'solids_pct' and '固形物(%)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'fat_protein_ratio' and '脂蛋比' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'urea_nitrogen' and '尿素氮(mg/dl)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'total_fat_pct' and '总乳脂(%)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'total_protein_pct' and '总蛋白(%)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
            elif trait == 'mature_equivalent' and '成年当量(Kg)' in col and '年' in col and '月' in col:
                monthly_columns.append(col)
        
        if not monthly_columns:
            stats_text += f"📊 筛选结果: {len(df)} 条记录\n"
            stats_text += f"❌ 未找到 {trait_name} 的月度数据列\n"
            stats_text += "请确认该性状已包含在筛选结果中。"
        else:
            # 按时间排序月度列
            monthly_columns.sort()
            
            # 基础统计
            stats_text += f"📊 筛选结果: {len(df)} 条记录\n"
            stats_text += f"📅 月度数据: {len(monthly_columns)} 个月\n\n"
            
            # 各月统计
            stats_text += f"📈 各月 {trait_name} 统计:\n"
            for col in monthly_columns:
                month_data = df[col].dropna()
                if len(month_data) > 0:
                    avg_val = month_data.mean()
                    min_val = month_data.min()
                    max_val = month_data.max()
                    count = len(month_data)
                    
                    # 根据性状类型格式化数值
                    if trait in ['protein_pct', 'fat_pct', 'lactose_pct', 'solids_pct', 'total_fat_pct', 'total_protein_pct']:
                        stats_text += f"  {col}: 平均 {avg_val:.2f}%，范围 {min_val:.2f}%-{max_val:.2f}%，{count}头牛\n"
                    elif trait in ['milk_yield', 'mature_equivalent']:
                        stats_text += f"  {col}: 平均 {avg_val:.1f}Kg，范围 {min_val:.1f}-{max_val:.1f}Kg，{count}头牛\n"
                    elif trait in ['lactation_days']:
                        stats_text += f"  {col}: 平均 {avg_val:.1f}天，范围 {min_val:.0f}-{max_val:.0f}天，{count}头牛\n"
                    elif trait in ['somatic_cell_count']:
                        stats_text += f"  {col}: 平均 {avg_val:.1f}万/ml，范围 {min_val:.1f}-{max_val:.1f}万/ml，{count}头牛\n"
                    elif trait in ['urea_nitrogen']:
                        stats_text += f"  {col}: 平均 {avg_val:.1f}mg/dl，范围 {min_val:.1f}-{max_val:.1f}mg/dl，{count}头牛\n"
                    elif trait in ['fat_protein_ratio']:
                        stats_text += f"  {col}: 平均 {avg_val:.2f}，范围 {min_val:.2f}-{max_val:.2f}，{count}头牛\n"
                    else:
                        stats_text += f"  {col}: 平均 {avg_val:.2f}，范围 {min_val:.2f}-{max_val:.2f}，{count}头牛\n"
                else:
                    stats_text += f"  {col}: 无有效数据\n"
            
            # 整体统计
            all_monthly_data = []
            for col in monthly_columns:
                month_data = df[col].dropna()
                all_monthly_data.extend(month_data.tolist())
            
            if all_monthly_data:
                overall_avg = sum(all_monthly_data) / len(all_monthly_data)
                overall_min = min(all_monthly_data)
                overall_max = max(all_monthly_data)
                
                stats_text += f"\n🎯 整体 {trait_name} 统计:\n"
                if trait in ['protein_pct', 'fat_pct', 'lactose_pct', 'solids_pct', 'total_fat_pct', 'total_protein_pct']:
                    stats_text += f"  总体平均: {overall_avg:.2f}%\n"
                    stats_text += f"  总体范围: {overall_min:.2f}% - {overall_max:.2f}%\n"
                elif trait in ['milk_yield', 'mature_equivalent']:
                    stats_text += f"  总体平均: {overall_avg:.1f}Kg\n"
                    stats_text += f"  总体范围: {overall_min:.1f}Kg - {overall_max:.1f}Kg\n"
                elif trait in ['lactation_days']:
                    stats_text += f"  总体平均: {overall_avg:.1f}天\n"
                    stats_text += f"  总体范围: {overall_min:.0f}天 - {overall_max:.0f}天\n"
                elif trait in ['somatic_cell_count']:
                    stats_text += f"  总体平均: {overall_avg:.1f}万/ml\n"
                    stats_text += f"  总体范围: {overall_min:.1f}万/ml - {overall_max:.1f}万/ml\n"
                elif trait in ['urea_nitrogen']:
                    stats_text += f"  总体平均: {overall_avg:.1f}mg/dl\n"
                    stats_text += f"  总体范围: {overall_min:.1f}mg/dl - {overall_max:.1f}mg/dl\n"
                elif trait in ['fat_protein_ratio']:
                    stats_text += f"  总体平均: {overall_avg:.2f}\n"
                    stats_text += f"  总体范围: {overall_min:.2f} - {overall_max:.2f}\n"
                else:
                    stats_text += f"  总体平均: {overall_avg:.2f}\n"
                    stats_text += f"  总体范围: {overall_min:.2f} - {overall_max:.2f}\n"
                
                stats_text += f"  有效数据点: {len(all_monthly_data)} 个\n"
        
        widget.setText(stats_text)
    
    # ==================== 慢性乳房炎筛查相关方法 ====================
    
    def on_mastitis_system_selected(self, system_type: str, checked: bool):
        """系统类型选择事件处理"""
        if not checked:
            return
        
        # 确保只能选择一个系统（单选模式）
        if system_type == 'yiqiniu':
            self.huimuyun_radio.setChecked(False)
            self.custom_radio.setChecked(False)
        elif system_type == 'huimuyun':
            self.yiqiniu_radio.setChecked(False)
            self.custom_radio.setChecked(False)
        elif system_type == 'custom':
            self.yiqiniu_radio.setChecked(False)
            self.huimuyun_radio.setChecked(False)
        
        self.current_mastitis_system = system_type
        self.create_mastitis_file_upload_widgets(system_type)
        self.mastitis_upload_group.setVisible(True)
        self.update_mastitis_screen_button_state()
    
    def create_mastitis_file_upload_widgets(self, system_type: str):
        """根据系统类型创建文件上传控件"""
        # 清除现有控件
        for widget in self.mastitis_file_uploads.values():
            widget.setParent(None)
        self.mastitis_file_uploads.clear()
        
        # 根据系统类型创建对应的上传控件和字段映射
        if system_type == 'yiqiniu':
            files_config = {
                'cattle_info': {
                    'name': '牛群基础信息表',
                    'fields': {
                        '耳号': '耳号（去掉最前面的"0"）',
                        '胎次': '胎次（去掉最前面的"0"）', 
                        '泌乳天数': '泌乳天数',
                        '繁育状态': '繁育状态',
                        '在胎天数': '在胎天数',
                        '最近产犊日期': '最近产犊日期'
                    }
                },
                'milk_yield': {
                    'name': '奶牛产奶日汇总表',
                    'fields': {
                        '耳号': '耳号（去掉最前面的"0"）',
                        '挤奶日期': '挤奶日期',
                        '日产量(kg)': '日产量（kg）'
                    }
                },
                'disease': {
                    'name': '发病查询导出表',
                    'fields': {
                        '耳号': '耳号（去掉最前面的"0"）',
                        '发病日期': '发病日期',
                        '疾病种类': '疾病种类'
                    }
                }
            }
        elif system_type == 'huimuyun':
            files_config = {
                'cattle_info': {
                    'name': '牛群基础信息表',
                    'fields': {
                        '耳号': '耳号（去掉最前面的"0"）',
                        '胎次': '胎次（去掉最前面的"0"）',
                        '泌乳天数': '泌乳天数',
                        '繁育状态': '繁育状态',
                        '在胎天数': '怀孕天数',
                        '最近产犊日期': '产犊日期',
                        '最近七天奶厅平均奶量': '最近七天奶厅平均奶量'
                    }
                },
                'disease': {
                    'name': '发病事件管理表',
                    'fields': {
                        '耳号': '耳号（去掉最前面的"0"）',
                        '事件日期': '事件日期',
                        '事件类型': '事件类型'
                    }
                }
            }
        elif system_type == 'custom':
            files_config = {
                'cattle_info': {
                    'name': '牛群基础信息表',
                    'fields': {
                        '耳号': '耳号',
                        '胎次': '胎次',
                        '泌乳天数': '泌乳天数',
                        '繁育状态': '繁育状态',
                        '在胎天数': '在胎天数',
                        '最近产犊日期': '最近产犊日期',
                        '最近七天奶厅平均奶量': '最近七天奶厅平均奶量'
                    },
                    'custom': True
                },
                'disease': {
                    'name': '发病查询导出表',
                    'fields': {
                        '耳号': '耳号',
                        '发病日期': '事件日期',
                        '疾病种类': '事件类型'
                    },
                    'custom': True
                }
            }
        else:
            return
        
        # 创建文件上传控件
        for file_key, file_config in files_config.items():
            file_widget = self.create_mastitis_file_upload_widget(file_key, file_config, system_type)
            self.mastitis_file_uploads[file_key] = file_widget
            self.mastitis_upload_layout.addWidget(file_widget)
    
    def create_mastitis_file_upload_widget(self, file_key: str, file_config: dict, system_type: str):
        """创建单个文件上传控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 文件名标签
        name_label = QLabel(f"📄 {file_config['name']}")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: black; background-color: white;")
        layout.addWidget(name_label)
        
        # 字段映射显示
        if file_config.get('custom', False):
            # 自定义系统，显示可编辑的字段映射
            mapping_label = QLabel("字段映射（所需数据 → 表头列名）：")
            mapping_label.setStyleSheet("font-weight: bold; color: black; margin-top: 8px; background-color: white;")
            layout.addWidget(mapping_label)
            
            # 创建字段映射编辑区域
            mapping_widget = QWidget()
            mapping_layout = QVBoxLayout(mapping_widget)
            mapping_layout.setContentsMargins(0, 0, 0, 0)
            
            # 存储映射输入控件
            mapping_inputs = {}
            
            for required_field, default_value in file_config['fields'].items():
                field_layout = QHBoxLayout()
                
                # 所需数据标签
                field_label = QLabel(f"{required_field}:")
                field_label.setFixedWidth(120)
                field_label.setStyleSheet("font-weight: bold; color: black; background-color: white;")
                field_layout.addWidget(field_label)
                
                # 箭头
                arrow_label = QLabel("→")
                arrow_label.setStyleSheet("color: black; font-size: 14px; background-color: white; font-weight: bold;")
                field_layout.addWidget(arrow_label)
                
                # 输入框
                input_edit = QLineEdit()
                input_edit.setPlaceholderText(f"请输入表头列名（如：{default_value}）")
                input_edit.setStyleSheet("""
                    QLineEdit {
                        padding: 4px 8px;
                        border: 1px solid #bdc3c7;
                        border-radius: 4px;
                        background-color: white;
                        color: black;
                        font-weight: bold;
                    }
                """)
                field_layout.addWidget(input_edit)
                
                mapping_inputs[required_field] = input_edit
                mapping_layout.addLayout(field_layout)
            
            mapping_widget.setLayout(mapping_layout)
            layout.addWidget(mapping_widget)
            
            # 保存映射输入控件的引用
            widget.mapping_inputs = mapping_inputs
            
        else:
            # 固定系统，只显示字段映射关系
            mapping_label = QLabel("字段映射（所需数据 → 表头列名）：")
            mapping_label.setStyleSheet("font-weight: bold; color: black; margin-top: 8px; background-color: white;")
            layout.addWidget(mapping_label)
            
            # 创建字段映射显示区域
            mapping_text = []
            for required_field, table_header in file_config['fields'].items():
                mapping_text.append(f"• {required_field} → {table_header}")
            
            mapping_display = QLabel("\n".join(mapping_text))
            mapping_display.setStyleSheet("""
                QLabel {
                    color: black;
                    font-size: 12px;
                    padding: 8px;
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    margin-bottom: 8px;
                    font-weight: bold;
                }
            """)
            layout.addWidget(mapping_display)
        
        # 分隔线
        separator = QWidget()
        separator.setStyleSheet("border-top: 1px solid #dee2e6; margin: 8px 0;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # 文件上传行
        upload_layout = QHBoxLayout()
        
        # 文件路径显示
        file_path_edit = QLineEdit()
        file_path_edit.setPlaceholderText("请选择文件...")
        file_path_edit.setReadOnly(True)
        file_path_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                color: black;
                font-weight: bold;
            }
        """)
        upload_layout.addWidget(file_path_edit)
        
        # 选择文件按钮
        select_btn = QPushButton("选择文件")
        select_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        select_btn.clicked.connect(lambda: self.select_mastitis_file(file_key, file_config['name']))
        upload_layout.addWidget(select_btn)
        
        layout.addLayout(upload_layout)
        
        # 状态标签
        status_label = QLabel("未选择")
        status_label.setStyleSheet("color: black; font-size: 12px; margin-top: 4px; background-color: white; font-weight: bold;")
        layout.addWidget(status_label)
        
        # 保存引用
        widget.file_path_edit = file_path_edit
        widget.select_btn = select_btn
        widget.status_label = status_label
        widget.file_config = file_config
        widget.file_path = None
        
        # 设置样式
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 4px;
            }
        """)
        
        return widget
    
    def select_mastitis_file(self, file_key: str, file_name: str):
        """选择文件"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, f"选择{file_name}", "", 
            "Excel文件 (*.xlsx *.xls);;所有文件 (*)"
        )
        
        if file_path:
            # 创建进度对话框
            file_process_dialog = SmoothProgressDialog(
                f"处理文件: {os.path.basename(file_path)}",
                "取消",
                0, 100,
                self
            )
            file_process_dialog.show()
            file_process_dialog.setLabelText("正在处理文件...")
            
            widget = self.mastitis_file_uploads[file_key]
            widget.file_path = file_path
            widget.file_path_edit.setText(os.path.basename(file_path))
            widget.status_label.setText(f"已选择: {os.path.basename(file_path)}")
            widget.status_label.setStyleSheet("color: #28a745; font-size: 12px;")
            
            # 更新进度 - 文件选择完成
            file_process_dialog.setValue(20)
            file_process_dialog.setLabelText("正在读取文件信息...")
            QApplication.processEvents()
            
            # 显示文件信息到右侧面板
            self.display_mastitis_file_info(file_key, file_name, file_path)
            
            # 更新进度 - 文件信息读取完成
            file_process_dialog.setValue(50)
            
            # 如果是牛群基础信息表，立即处理并保存数据
            if file_key == 'cattle_info':
                file_process_dialog.setLabelText("正在处理牛群基础信息...")
                file_process_dialog.setValue(60)
                QApplication.processEvents()
                
                # 立即处理牛群基础信息表
                success = self.process_and_save_cattle_basic_info(file_path)
                
                if success:
                    file_process_dialog.setLabelText("正在提取繁育状态...")
                    file_process_dialog.setValue(80)
                    QApplication.processEvents()
                    self.extract_and_update_breeding_status(file_path)
                    file_process_dialog.setValue(100)
                    file_process_dialog.setLabelText("牛群基础信息处理完成")
                else:
                    file_process_dialog.setValue(100)
                    file_process_dialog.setLabelText("牛群基础信息处理失败")
            else:
                file_process_dialog.setValue(100)
                file_process_dialog.setLabelText("文件处理完成")
            
            # 延迟关闭进度对话框
            QTimer.singleShot(2000, lambda: file_process_dialog.close())
            
            self.update_mastitis_screen_button_state()
    
    

    def display_mastitis_file_info(self, file_key: str, file_name: str, file_path: str):
        """显示慢性乳房炎文件信息到右侧面板"""
        try:
            import os
            import pandas as pd
            from datetime import datetime
            
            # 创建进度对话框
            progress_dialog = SmoothProgressDialog(
                f"正在读取文件: {os.path.basename(file_path)}",
                "取消",
                0, 100,
                self
            )
            progress_dialog.show()
            
            # 获取文件基本信息
            progress_dialog.setLabelText("获取文件信息...")
            progress_dialog.setValue(20)
            QApplication.processEvents()
            
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # 读取Excel文件获取数据信息
            progress_dialog.setLabelText("读取文件内容...")
            progress_dialog.setValue(50)
            QApplication.processEvents()
            
            try:
                if file_key == 'milk_yield' and self.current_mastitis_system == 'yiqiniu':
                    # 奶牛产奶日汇总表可能有多个sheet
                    with pd.ExcelFile(file_path) as xls:
                        sheet_names = xls.sheet_names
                        total_rows = 0
                        sheet_info = []
                        for i, sheet_name in enumerate(sheet_names):
                            progress_value = 50 + int(40 * (i + 1) / len(sheet_names))
                            progress_dialog.setValue(progress_value)
                            progress_dialog.setLabelText(f"读取工作表: {sheet_name}")
                            QApplication.processEvents()
                            
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                            total_rows += len(df)
                            sheet_info.append(f"  - {sheet_name}: {len(df)}行")
                        
                        data_info = f"数据信息: {len(sheet_names)}个工作表，共{total_rows}行数据\n"
                        data_info += "\n".join(sheet_info)
                else:
                    # 单个sheet
                    df = pd.read_excel(file_path)
                    data_info = f"数据信息: {len(df)}行 × {len(df.columns)}列"
                    if len(df) > 0:
                        # 显示前几个列名
                        columns_preview = ", ".join(df.columns[:5].tolist())
                        if len(df.columns) > 5:
                            columns_preview += "..."
                        data_info += f"\n列名预览: {columns_preview}"
            except Exception as e:
                data_info = f"数据信息: 读取失败 - {str(e)}"
            
            progress_dialog.setValue(100)
            progress_dialog.close()
            
            # 构建信息文本
            info_text = f"""
🆕 慢性乳房炎筛查文件上传
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 文件类型: {file_name}
📁 文件名: {os.path.basename(file_path)}
📊 文件大小: {file_size_mb:.2f} MB
📅 修改时间: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}
🗂️ 完整路径: {file_path}

{data_info}

⚙️ 系统类型: {self.current_mastitis_system}
🔄 状态: 已上传，等待处理

"""
            
            # 显示到右侧文件信息面板
            self.file_info_widget.append(info_text)
            
            # 自动切换到文件信息标签页
            self.tab_widget.setCurrentWidget(self.file_info_widget)
            
        except Exception as e:
            error_text = f"""
❌ 文件信息获取失败
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 文件名: {os.path.basename(file_path)}
❌ 错误: {str(e)}

"""
            self.file_info_widget.append(error_text)
    
    def process_and_save_cattle_basic_info(self, file_path: str) -> bool:
        """立即处理并保存牛群基础信息到主窗口"""
        try:
            print(f"\n🔄 [立即处理] 开始处理牛群基础信息表...")
            print(f"   文件路径: {file_path}")
            print(f"   当前系统: {self.current_mastitis_system}")
            print(f"   文件是否存在: {os.path.exists(file_path)}")
            
            # 检查当前主窗口状态
            print(f"🔍 [处理前] 主窗口状态检查...")
            print(f"   hasattr(self, 'cattle_basic_info'): {hasattr(self, 'cattle_basic_info')}")
            print(f"   hasattr(self, 'current_system'): {hasattr(self, 'current_system')}")
            print(f"   hasattr(self, 'data_processor'): {hasattr(self, 'data_processor')}")
            
            # 直接处理牛群基础信息文件（不依赖其他文件）
            print(f"   🔄 直接处理牛群基础信息文件...")
            
            if self.current_mastitis_system == 'yiqiniu':
                # 伊起牛系统：直接调用牛群基础信息处理方法
                success, message, cattle_df = self.data_processor._process_yiqiniu_cattle_info(file_path)
                processed_data = {'cattle_info': cattle_df} if success else {}
                
            elif self.current_mastitis_system == 'huimuyun':
                # 慧牧云系统：直接调用牛群基础信息处理方法
                success, message, cattle_df = self.data_processor._process_huimuyun_cattle_info(file_path)
                processed_data = {'cattle_info': cattle_df} if success else {}
                
            elif self.current_mastitis_system == 'custom':
                # 自定义系统需要字段映射
                widget = self.mastitis_file_uploads.get('cattle_info')
                if widget and hasattr(widget, 'mapping_inputs'):
                    field_mappings = {}
                    for field, input_widget in widget.mapping_inputs.items():
                        column_name = input_widget.text().strip()
                        if column_name:
                            field_mappings[field] = column_name
                    
                    success, message, cattle_df = self.data_processor._process_custom_cattle_info(
                        file_path, field_mappings
                    )
                    processed_data = {'cattle_info': cattle_df} if success else {}
                else:
                    print(f"   ❌ 自定义系统缺少字段映射配置")
                    return False
            else:
                print(f"   ❌ 未知系统类型: {self.current_mastitis_system}")
                return False
            
            if success and 'cattle_info' in processed_data:
                # 保存牛群基础信息到主窗口
                self.cattle_basic_info = processed_data['cattle_info']
                self.current_system = self.current_mastitis_system
                
                print(f"✅ [立即处理] 牛群基础信息已保存到主窗口: {len(self.cattle_basic_info)}头牛")
                print(f"✅ [立即处理] 系统类型已保存: {self.current_system}")
                
                # 更新隐形乳房炎监测的数据状态显示
                if hasattr(self, 'update_monitoring_data_status'):
                    self.update_monitoring_data_status()
                
                # 在处理过程面板中显示成功信息
                self.process_log_widget.append(f"""
🎉 牛群基础信息立即处理成功
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 文件: {os.path.basename(file_path)}
⚙️ 系统: {self.current_mastitis_system}
🐄 牛只数量: {len(self.cattle_basic_info)}头
✅ 状态: 已自动保存，可用于隐形乳房炎监测

💡 现在您可以到"隐形乳房炎监测"功能中上传DHI数据进行分析了！
""")
                
                return True
            else:
                print(f"   ❌ 牛群基础信息处理失败: {message}")
                return False
                
        except Exception as e:
            print(f"   ❌ 处理牛群基础信息时出错: {str(e)}")
            return False

    def extract_and_update_breeding_status(self, file_path: str):
        """提取牛群基础信息表中的繁殖状态并更新选项"""
        try:
            # 在处理过程中显示操作信息
            self.process_log_widget.append(f"""
🔄 自动提取繁育状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 文件: {os.path.basename(file_path)}
⚙️ 系统: {self.current_mastitis_system}
🔍 开始提取...
""")
            
            # 切换到处理过程标签页
            self.tab_widget.setCurrentWidget(self.process_log_widget)
            
            # 读取Excel文件
            self.process_log_widget.append("📖 正在读取Excel文件...")
            df = pd.read_excel(file_path)
            self.process_log_widget.append(f"✅ 成功读取文件，共 {len(df)} 行数据")
            
            # 根据当前系统类型确定繁殖状态列名
            breeding_status_col = None
            if self.current_mastitis_system == 'yiqiniu':
                breeding_status_col = '繁育状态'
            elif self.current_mastitis_system == 'huimuyun':
                breeding_status_col = '繁育状态'
            elif self.current_mastitis_system == 'custom':
                # 自定义系统，从字段映射中获取
                widget = self.mastitis_file_uploads.get('cattle_info')
                if widget and hasattr(widget, 'mapping_inputs'):
                    input_widget = widget.mapping_inputs.get('繁育状态')
                    if input_widget:
                        breeding_status_col = input_widget.text().strip()
            
            self.process_log_widget.append(f"🔍 查找繁育状态列: {breeding_status_col}")
            
            if not breeding_status_col:
                error_msg = "❌ 未找到繁殖状态列名映射"
                self.process_log_widget.append(error_msg)
                return
                
            if breeding_status_col not in df.columns:
                error_msg = f"❌ 文件中未找到列 '{breeding_status_col}'"
                self.process_log_widget.append(f"📋 可用列名: {list(df.columns)}")
                self.process_log_widget.append(error_msg)
                return
            
            # 提取所有不同的繁殖状态值
            self.process_log_widget.append("🔍 正在分析繁育状态数据...")
            unique_statuses = df[breeding_status_col].dropna().unique()
            unique_statuses = [str(status).strip() for status in unique_statuses if str(status).strip()]
            unique_statuses = sorted(set(unique_statuses))  # 去重并排序
            
            if unique_statuses:
                success_msg = f"✅ 成功提取繁殖状态选项: {', '.join(unique_statuses)}"
                self.process_log_widget.append(success_msg)
                
                # 更新所有处置办法的繁殖状态选项
                self.process_log_widget.append("🔄 正在更新处置办法配置...")
                try:
                    self.update_breeding_status_options(unique_statuses)
                    self.process_log_widget.append("✅ 处置办法配置更新完成")
                except Exception as update_error:
                    error_msg = f"❌ 更新处置办法配置时出错: {str(update_error)}"
                    self.process_log_widget.append(error_msg)
                    print(f"更新处置办法配置时出错: {update_error}")
            else:
                warning_msg = "⚠️ 未找到有效的繁殖状态数据"
                self.process_log_widget.append(warning_msg)
                
        except Exception as e:
            error_msg = f"❌ 提取繁殖状态时出错: {str(e)}"
            self.process_log_widget.append(error_msg)
            print(f"提取繁殖状态时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def update_breeding_status_options(self, statuses: List[str]):
        """更新所有处置办法的繁殖状态选项"""
        try:
            print(f"开始更新繁殖状态选项: {statuses}")
            
            for method_key, widget in self.treatment_configs.items():
                print(f"处理处置办法: {method_key}")
                
                if hasattr(widget, 'breeding_checkboxes'):
                    # 清除现有的复选框
                    print(f"清除现有复选框: {len(widget.breeding_checkboxes)}个")
                    for cb in widget.breeding_checkboxes.values():
                        if cb is not None:
                            cb.setParent(None)
                    widget.breeding_checkboxes.clear()
                    
                    # 找到繁殖状态布局容器 - 使用更简单的方法
                    breeding_status_widget = None
                    config_layout = widget.config_widget.layout()
                    
                    if config_layout is not None:
                        # 直接查找标签为"繁殖状态:"的行
                        for i in range(config_layout.rowCount()):
                            label_item = config_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                            field_item = config_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
                            
                            if label_item and label_item.widget():
                                label_text = label_item.widget().text()
                                if "繁殖状态" in label_text and field_item and field_item.widget():
                                    breeding_status_widget = field_item.widget()
                                    print(f"找到繁殖状态控件: {breeding_status_widget}")
                                    break
                    
                    if breeding_status_widget:
                        # 获取或创建布局
                        layout = breeding_status_widget.layout()
                        if layout is None:
                            # 如果没有布局，创建新的
                            layout = QGridLayout(breeding_status_widget)
                            layout.setContentsMargins(0, 0, 0, 0)
                            print("创建新的网格布局")
                        else:
                            # 如果有布局，清空内容
                            print(f"清空现有布局，有 {layout.count()} 个项目")
                            while layout.count():
                                item = layout.takeAt(0)
                                if item and item.widget():
                                    item.widget().setParent(None)
                        
                        # 重新创建复选框
                        widget.breeding_checkboxes = {}
                        print(f"创建 {len(statuses)} 个新的复选框")
                        for i, status in enumerate(statuses):
                            cb = QCheckBox(status)
                            cb.setChecked(True)  # 默认全选
                            widget.breeding_checkboxes[status] = cb
                            
                            # 计算行列位置（每行3个）
                            row = i // 3
                            col = i % 3
                            layout.addWidget(cb, row, col)
                        
                        print(f"成功更新 {method_key} 的繁殖状态选项")
                    else:
                        print(f"未找到 {method_key} 的繁殖状态控件")
                else:
                    print(f"{method_key} 没有 breeding_checkboxes 属性")
            
            print("繁殖状态选项更新完成")
            
        except Exception as e:
            print(f"update_breeding_status_options 出错: {e}")
            import traceback
            traceback.print_exc()
            raise

    def update_chronic_months_options(self, available_months: List[str]):
        """更新慢性感染牛识别的月份选择选项"""
        print(f"开始更新慢性感染牛月份选项: {available_months}")
        
        # 检查chronic_months_widget是否存在
        if not hasattr(self, 'chronic_months_widget'):
            print("chronic_months_widget不存在，跳过月份选项更新")
            return
        
        # 清空现有布局
        layout = self.chronic_months_widget.layout()
        for i in reversed(range(layout.count())):
            item = layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        # 清空复选框字典
        self.chronic_month_checkboxes = {}
        
        if not available_months:
            # 没有数据时显示提示信息
            no_data_label = QLabel("请先上传DHI数据以选择月份")
            no_data_label.setStyleSheet("color: #6c757d; font-style: italic;")
            layout.addWidget(no_data_label, 0, 0, 1, 3)
            print("没有可用月份，显示提示信息")
            return
        
        # 创建月份复选框，按年-月排序
        sorted_months = sorted(available_months)
        last_month = sorted_months[-1] if sorted_months else None  # 获取最后一个月份（最新数据）
        print(f"按顺序创建 {len(sorted_months)} 个月份复选框，默认选择最新月份: {last_month}")

        for i, month in enumerate(sorted_months):
            cb = QCheckBox(month)
            cb.setChecked(month == last_month)  # 默认只选择最新月份
            self.chronic_month_checkboxes[month] = cb

            # 计算行列位置（每行4个）
            row = i // 4
            col = i % 4
            layout.addWidget(cb, row, col)

        print(f"成功创建 {len(sorted_months)} 个月份复选框，默认选择: {last_month}")
        
        # 添加全选/全不选按钮
        button_row = (len(sorted_months) - 1) // 4 + 1
        
        select_all_btn = QPushButton("全选")
        select_all_btn.setMaximumWidth(60)
        select_all_btn.clicked.connect(lambda: self._set_all_chronic_months(True))
        layout.addWidget(select_all_btn, button_row, 0)
        
        select_none_btn = QPushButton("全不选")
        select_none_btn.setMaximumWidth(60)
        select_none_btn.clicked.connect(lambda: self._set_all_chronic_months(False))
        layout.addWidget(select_none_btn, button_row, 1)
        
        print("月份选项更新完成")

    def _set_all_chronic_months(self, checked: bool):
        """设置所有慢性感染牛月份复选框的状态"""
        for month, cb in self.chronic_month_checkboxes.items():
            cb.setChecked(checked)
    
    def create_treatment_config_widget(self, method_key: str, method_name: str, icon: str, form_styles: str):
        """创建处置办法配置控件"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                margin: 5px 0;
                background-color: #fafafa;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)

        # 繁殖状态提示信息
        breeding_hints = {
            'cull': '适用于：未孕牛',
            'isolate': '适用于：未孕牛',
            'blind_quarter': '适用于：怀孕牛',
            'early_dry': '适用于：怀孕牛',
            'treatment': '适用于：怀孕牛'
        }

        # 标题行
        title_layout = QHBoxLayout()

        # 启用复选框
        enabled_cb = QCheckBox(f"{icon} {method_name}")
        enabled_cb.setStyleSheet("font-weight: bold; color: black; background-color: white;")
        enabled_cb.setChecked(True)  # 默认启用
        title_layout.addWidget(enabled_cb)

        # 添加繁殖状态提示
        hint_label = QLabel(breeding_hints.get(method_key, ''))
        hint_label.setStyleSheet("color: #6c757d; font-size: 11px; font-style: italic; background-color: transparent;")
        title_layout.addWidget(hint_label)

        title_layout.addStretch()

        layout.addLayout(title_layout)
        
        # 配置区域（默认显示）
        config_widget = QWidget()
        config_widget.setStyleSheet("""
            QWidget {
                text-align: left;
                alignment: left;
            }
        """)
        config_layout = QFormLayout(config_widget)
        config_layout.setContentsMargins(20, 10, 10, 10)
        config_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # 设置标签左对齐
        config_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # 设置表单左对齐
        config_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)  # 字段扩展策略
        
        # 根据处置办法类型创建对应的配置项
        if method_key == 'cull':  # 淘汰
            # 产奶量条件
            yield_layout = QHBoxLayout()
            yield_combo = QComboBox()
            yield_combo.addItems(["<", "<=", "=", ">=", ">"])
            yield_combo.setCurrentText("<=")
            yield_combo.setStyleSheet(form_styles)
            yield_combo.setFixedWidth(70)
            
            yield_spin = QDoubleSpinBox()
            yield_spin.setRange(0, 100)
            yield_spin.setValue(15)
            yield_spin.setSuffix("kg")
            yield_spin.setStyleSheet(form_styles)
            
            yield_layout.addWidget(yield_combo)
            yield_layout.addWidget(yield_spin)
            yield_layout.addStretch()
            
            yield_widget = QWidget()
            yield_widget.setLayout(yield_layout)
            yield_label = QLabel("产奶量:")
            yield_label.setStyleSheet("color: black; background-color: white; font-weight: bold;")
            config_layout.addRow(yield_label, yield_widget)
            widget.yield_combo = yield_combo
            widget.yield_spin = yield_spin
            
        elif method_key == 'isolate':  # 禁配隔离
            # 产奶量条件
            yield_layout = QHBoxLayout()
            yield_combo = QComboBox()
            yield_combo.addItems(["<", "<=", "=", ">=", ">"])
            yield_combo.setCurrentText(">=")
            yield_combo.setStyleSheet(form_styles)
            yield_combo.setFixedWidth(70)
            
            yield_spin = QDoubleSpinBox()
            yield_spin.setRange(0, 100)
            yield_spin.setValue(15)
            yield_spin.setSuffix("kg")
            yield_spin.setStyleSheet(form_styles)
            
            yield_layout.addWidget(yield_combo)
            yield_layout.addWidget(yield_spin)
            yield_layout.addStretch()
            
            yield_widget = QWidget()
            yield_widget.setLayout(yield_layout)
            yield_label2 = QLabel("产奶量:")
            yield_label2.setStyleSheet("color: black; background-color: white; font-weight: bold;")
            config_layout.addRow(yield_label2, yield_widget)
            widget.yield_combo = yield_combo
            widget.yield_spin = yield_spin
            
        elif method_key == 'blind_quarter':  # 瞎乳区
            # 产奶量条件（需求：>=15kg）
            yield_layout = QHBoxLayout()
            yield_combo = QComboBox()
            yield_combo.addItems(["<", "<=", "=", ">=", ">"])
            yield_combo.setCurrentText(">=")
            yield_combo.setStyleSheet(form_styles)
            yield_combo.setFixedWidth(70)

            yield_spin = QDoubleSpinBox()
            yield_spin.setRange(0, 100)
            yield_spin.setValue(15)
            yield_spin.setSuffix("kg")
            yield_spin.setStyleSheet(form_styles)

            yield_layout.addWidget(yield_combo)
            yield_layout.addWidget(yield_spin)
            yield_layout.addStretch()

            yield_widget = QWidget()
            yield_widget.setLayout(yield_layout)
            yield_label = QLabel("产奶量:")
            yield_label.setStyleSheet("color: black; background-color: white; font-weight: bold;")
            config_layout.addRow(yield_label, yield_widget)
            widget.yield_combo = yield_combo
            widget.yield_spin = yield_spin

            # 在胎天数条件（需求：<180天）
            gestation_layout = QHBoxLayout()
            gestation_combo = QComboBox()
            gestation_combo.addItems(["<", "<=", "=", ">=", ">"])
            gestation_combo.setCurrentText("<")
            gestation_combo.setStyleSheet(form_styles)
            gestation_combo.setFixedWidth(70)

            gestation_spin = QSpinBox()
            gestation_spin.setRange(0, 300)
            gestation_spin.setValue(180)
            gestation_spin.setSuffix("天")
            gestation_spin.setStyleSheet(form_styles)

            gestation_layout.addWidget(gestation_combo)
            gestation_layout.addWidget(gestation_spin)
            gestation_layout.addStretch()

            gestation_widget = QWidget()
            gestation_widget.setLayout(gestation_layout)
            config_layout.addRow("在胎天数:", gestation_widget)
            widget.gestation_combo = gestation_combo
            widget.gestation_spin = gestation_spin
            
        elif method_key == 'early_dry':  # 提前干奶
            # 产奶量条件（需求：>=0kg）
            yield_layout = QHBoxLayout()
            yield_combo = QComboBox()
            yield_combo.addItems(["<", "<=", "=", ">=", ">"])
            yield_combo.setCurrentText(">=")
            yield_combo.setStyleSheet(form_styles)
            yield_combo.setFixedWidth(70)

            yield_spin = QDoubleSpinBox()
            yield_spin.setRange(0, 100)
            yield_spin.setValue(0)
            yield_spin.setSuffix("kg")
            yield_spin.setStyleSheet(form_styles)

            yield_layout.addWidget(yield_combo)
            yield_layout.addWidget(yield_spin)
            yield_layout.addStretch()

            yield_widget = QWidget()
            yield_widget.setLayout(yield_layout)
            yield_label = QLabel("产奶量:")
            yield_label.setStyleSheet("color: black; background-color: white; font-weight: bold;")
            config_layout.addRow(yield_label, yield_widget)
            widget.yield_combo = yield_combo
            widget.yield_spin = yield_spin

            # 在胎天数条件（需求：>=180天）
            gestation_layout = QHBoxLayout()
            gestation_combo = QComboBox()
            gestation_combo.addItems(["<", "<=", "=", ">=", ">"])
            gestation_combo.setCurrentText(">=")
            gestation_combo.setStyleSheet(form_styles)
            gestation_combo.setFixedWidth(70)

            gestation_spin = QSpinBox()
            gestation_spin.setRange(0, 300)
            gestation_spin.setValue(180)
            gestation_spin.setSuffix("天")
            gestation_spin.setStyleSheet(form_styles)

            gestation_layout.addWidget(gestation_combo)
            gestation_layout.addWidget(gestation_spin)
            gestation_layout.addStretch()

            gestation_widget = QWidget()
            gestation_widget.setLayout(gestation_layout)
            config_layout.addRow("在胎天数:", gestation_widget)
            widget.gestation_combo = gestation_combo
            widget.gestation_spin = gestation_spin

        elif method_key == 'treatment':  # 治疗
            # 产奶量条件（需求：>=0kg）
            yield_layout = QHBoxLayout()
            yield_combo = QComboBox()
            yield_combo.addItems(["<", "<=", "=", ">=", ">"])
            yield_combo.setCurrentText(">=")
            yield_combo.setStyleSheet(form_styles)
            yield_combo.setFixedWidth(70)

            yield_spin = QDoubleSpinBox()
            yield_spin.setRange(0, 100)
            yield_spin.setValue(0)
            yield_spin.setSuffix("kg")
            yield_spin.setStyleSheet(form_styles)

            yield_layout.addWidget(yield_combo)
            yield_layout.addWidget(yield_spin)
            yield_layout.addStretch()

            yield_widget = QWidget()
            yield_widget.setLayout(yield_layout)
            yield_label = QLabel("产奶量:")
            yield_label.setStyleSheet("color: black; background-color: white; font-weight: bold;")
            config_layout.addRow(yield_label, yield_widget)
            widget.yield_combo = yield_combo
            widget.yield_spin = yield_spin

            # 在胎天数条件（需求：>=0天）
            gestation_layout = QHBoxLayout()
            gestation_combo = QComboBox()
            gestation_combo.addItems(["<", "<=", "=", ">=", ">"])
            gestation_combo.setCurrentText(">=")
            gestation_combo.setStyleSheet(form_styles)
            gestation_combo.setFixedWidth(70)

            gestation_spin = QSpinBox()
            gestation_spin.setRange(0, 300)
            gestation_spin.setValue(0)
            gestation_spin.setSuffix("天")
            gestation_spin.setStyleSheet(form_styles)

            gestation_layout.addWidget(gestation_combo)
            gestation_layout.addWidget(gestation_spin)
            gestation_layout.addStretch()

            gestation_widget = QWidget()
            gestation_widget.setLayout(gestation_layout)
            config_layout.addRow("在胎天数:", gestation_widget)
            widget.gestation_combo = gestation_combo
            widget.gestation_spin = gestation_spin

        # 公共配置项
        # 发病次数条件（治疗默认<=2，其他默认>=2）
        mastitis_layout = QHBoxLayout()
        mastitis_combo = QComboBox()
        mastitis_combo.addItems(["<", "<=", "=", ">=", ">"])
        # 治疗的发病次数默认 <=2，其他默认 >=2
        if method_key == 'treatment':
            mastitis_combo.setCurrentText("<=")
        else:
            mastitis_combo.setCurrentText(">=")
        mastitis_combo.setStyleSheet(form_styles)
        mastitis_combo.setFixedWidth(70)

        mastitis_spin = QSpinBox()
        mastitis_spin.setRange(0, 10)
        mastitis_spin.setValue(2)
        mastitis_spin.setSuffix("次")
        mastitis_spin.setStyleSheet(form_styles)

        mastitis_layout.addWidget(mastitis_combo)
        mastitis_layout.addWidget(mastitis_spin)
        mastitis_layout.addStretch()

        mastitis_widget = QWidget()
        mastitis_widget.setLayout(mastitis_layout)
        config_layout.addRow("发病次数:", mastitis_widget)
        widget.mastitis_combo = mastitis_combo
        widget.mastitis_spin = mastitis_spin

        # 泌乳天数条件（瞎乳区/提前干奶/治疗默认>=0，淘汰/禁配隔离默认>=200）
        lactation_layout = QHBoxLayout()
        lactation_combo = QComboBox()
        lactation_combo.addItems(["<", "<=", "=", ">=", ">"])
        lactation_combo.setCurrentText(">=")
        lactation_combo.setStyleSheet(form_styles)
        lactation_combo.setFixedWidth(70)

        lactation_spin = QSpinBox()
        lactation_spin.setRange(0, 500)
        # 瞎乳区/提前干奶/治疗的泌乳天数默认 >=0，淘汰/禁配隔离默认 >=200
        if method_key in ['blind_quarter', 'early_dry', 'treatment']:
            lactation_spin.setValue(0)
        else:
            lactation_spin.setValue(200)
        lactation_spin.setSuffix("天")
        lactation_spin.setStyleSheet(form_styles)

        lactation_layout.addWidget(lactation_combo)
        lactation_layout.addWidget(lactation_spin)
        lactation_layout.addStretch()

        lactation_widget = QWidget()
        lactation_widget.setLayout(lactation_layout)
        config_layout.addRow("泌乳天数:", lactation_widget)
        widget.lactation_combo = lactation_combo
        widget.lactation_spin = lactation_spin

        # 繁殖状态多选
        breeding_status_label = QLabel("繁殖状态:")
        breeding_status_widget = QWidget()
        breeding_status_layout = QGridLayout(breeding_status_widget)
        breeding_status_layout.setContentsMargins(0, 0, 0, 0)

        # 根据处置办法类型设置不同的默认繁殖状态
        # 淘汰/禁配隔离：产犊、禁配、可配、已配、产后未配、初检空怀、发情未配、流产未配、已配未检
        # 瞎乳区/提前干奶/治疗：初检孕、复检孕、干奶、妊娠
        if method_key in ['cull', 'isolate']:
            default_statuses = ['产犊', '禁配', '可配', '已配', '产后未配', '初检空怀', '发情未配', '流产未配', '已配未检']
        else:
            default_statuses = ['初检孕', '复检孕', '干奶', '妊娠']

        widget.breeding_checkboxes = {}

        for i, status in enumerate(default_statuses):
            cb = QCheckBox(status)
            cb.setChecked(True)  # 默认全选
            widget.breeding_checkboxes[status] = cb

            # 计算行列位置（每行3个）
            row = i // 3
            col = i % 3
            breeding_status_layout.addWidget(cb, row, col)

        config_layout.addRow(breeding_status_label, breeding_status_widget)
        
        # 启用/禁用配置区域
        enabled_cb.toggled.connect(lambda checked: config_widget.setVisible(checked))
        config_widget.setVisible(True)  # 默认显示
        
        layout.addWidget(config_widget)
        
        # 存储引用
        widget.enabled_cb = enabled_cb
        widget.config_widget = config_widget
        
        return widget
    
    def update_mastitis_screen_button_state(self):
        """更新筛查按钮状态"""
        # 检查系统选择和文件上传状态
        system_selected = self.current_mastitis_system is not None
        
        if not system_selected:
            self.mastitis_screen_btn.setEnabled(False)
            self.mastitis_status_label.setText("请选择数据管理系统")
            return
        
        # 检查文件上传状态
        all_files_uploaded = True
        missing_files = []
        
        for file_key, widget in self.mastitis_file_uploads.items():
            if not hasattr(widget, 'file_path') or widget.file_path is None:
                all_files_uploaded = False
                missing_files.append(file_key)
        
        if not all_files_uploaded:
            self.mastitis_screen_btn.setEnabled(False)
            self.mastitis_status_label.setText(f"请上传缺失的文件: {', '.join(missing_files)}")
            return
        
        # 检查DHI数据是否已上传
        dhi_data_available = hasattr(self, 'data_list') and self.data_list
        
        if not dhi_data_available:
            self.mastitis_screen_btn.setEnabled(False)
            self.mastitis_status_label.setText("请先在基础数据标签页上传DHI报告")
            return
        
        # 所有条件满足
        self.mastitis_screen_btn.setEnabled(True)
        self.mastitis_status_label.setText("准备就绪，可以开始筛查")
    
    def start_mastitis_screening(self):
        """开始慢性乳房炎筛查"""
        try:
            # 清空右侧处理过程面板并切换到该标签页
            self.process_log_widget.clear()
            self.tab_widget.setCurrentWidget(self.process_log_widget)
            
            # 显示开始信息
            start_message = f"""
🏥 慢性乳房炎筛查开始
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ 系统类型: {self.current_mastitis_system}
📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔄 正在处理数据文件...
"""
            self.process_log_widget.append(start_message)
            
            # 创建进度对话框
            self.mastitis_progress_dialog = SmoothProgressDialog(
                "慢性乳房炎筛查",
                "取消",
                0, 100,
                self
            )
            self.mastitis_progress_dialog.setWindowTitle("慢性乳房炎筛查进度")
            self.mastitis_progress_dialog.show()
            
            # 更新进度
            self.mastitis_progress_dialog.setLabelText("步骤 1/8: 收集文件路径...")
            self.mastitis_progress_dialog.setValue(5)
            QApplication.processEvents()
            
            # 收集文件路径和字段映射
            file_paths = {}
            field_mappings = {}
            
            for file_key, widget in self.mastitis_file_uploads.items():
                file_paths[file_key] = widget.file_path
                
                # 如果是自定义系统，收集字段映射
                if hasattr(widget, 'mapping_inputs'):
                    field_mappings[file_key] = {}
                    for field, input_widget in widget.mapping_inputs.items():
                        column_name = input_widget.text().strip()
                        if column_name:
                            field_mappings[file_key][field] = column_name
            
            # 处理系统文件
            self.mastitis_progress_dialog.setValue(10)
            self.mastitis_progress_dialog.setLabelText("步骤 2/8: 处理系统文件...")
            self.process_log_widget.append("📂 开始处理系统文件...")
            QApplication.processEvents()
            
            success, message, processed_data = self.data_processor.process_mastitis_system_files(
                self.current_mastitis_system, file_paths, field_mappings
            )
            
            if not success:
                error_msg = f"❌ 文件处理失败: {message}"
                self.process_log_widget.append(error_msg)
                QMessageBox.warning(self, "文件处理失败", message)
                self.mastitis_progress_dialog.close()
                return
            
            self.process_log_widget.append(f"✅ 系统文件处理成功: {message}")
            
            # 保存牛群基础信息到主窗口，供监测功能使用
            self.cattle_basic_info = processed_data['cattle_info']
            self.current_system = self.current_mastitis_system
            print(f"🔍 牛群基础信息已保存到主窗口: {len(self.cattle_basic_info)}头牛")
            print(f"🔍 系统类型已保存: {self.current_system}")
            
            # 更新隐形乳房炎监测的数据状态显示
            if hasattr(self, 'update_monitoring_data_status'):
                self.update_monitoring_data_status()
            
            self.mastitis_progress_dialog.setValue(30)
            self.mastitis_progress_dialog.setLabelText("步骤 3/8: 计算最近7天奶量...")
            self.process_log_widget.append("🧮 正在计算关键指标...")
            QApplication.processEvents()
            
            # 计算最近7天平均奶量（仅伊起牛系统需要）
            if self.current_mastitis_system == 'yiqiniu':
                self.process_log_widget.append("🥛 计算最近7天平均奶量...")
                milk_yield_df = self.data_processor.calculate_recent_7day_avg_yield(processed_data['milk_yield'])
                # 合并到牛群信息中
                processed_data['cattle_info'] = processed_data['cattle_info'].merge(
                    milk_yield_df, on='ear_tag', how='left'
                )
                self.process_log_widget.append(f"✅ 完成{len(milk_yield_df)}头牛的奶量计算")
            
            self.mastitis_progress_dialog.setValue(50)
            self.mastitis_progress_dialog.setLabelText("步骤 4/8: 统计乳房炎发病...")
            QApplication.processEvents()
            
            # 计算乳房炎发病次数
            self.process_log_widget.append("🦠 计算乳房炎发病次数...")
            mastitis_count_df = self.data_processor.calculate_mastitis_count_per_lactation(
                processed_data['cattle_info'], processed_data['disease']
            )
            
            # 合并到牛群信息中
            processed_data['cattle_info'] = processed_data['cattle_info'].merge(
                mastitis_count_df, on='ear_tag', how='left'
            )
            
            affected_cows = len(mastitis_count_df[mastitis_count_df['mastitis_count'] > 0])
            total_cases = mastitis_count_df['mastitis_count'].sum()
            self.process_log_widget.append(f"✅ 发病统计完成: {affected_cows}头牛发病，共{total_cases}次")
            
            self.mastitis_progress_dialog.setValue(70)
            self.mastitis_progress_dialog.setLabelText("步骤 6/8: 识别慢性感染牛...")
            QApplication.processEvents()
            self.process_log_widget.append("🔬 识别慢性感染牛...")
            
            # 收集选中的月份
            selected_months = [month for month, cb in self.chronic_month_checkboxes.items() if cb.isChecked()]
            scc_operator = self.scc_threshold_combo.currentText()
            scc_threshold = self.scc_threshold_spin.value()
            
            if not selected_months:
                error_msg = "❌ 请至少选择一个月份进行慢性感染牛识别"
                self.process_log_widget.append(error_msg)
                self.show_warning("月份选择错误", "请至少选择一个月份进行慢性感染牛识别")
                self.mastitis_progress_dialog.close()
                return
            
            self.process_log_widget.append(f"🗓️ 检查月份: {', '.join(selected_months)}")
            self.process_log_widget.append(f"🔢 体细胞数条件: {scc_operator} {scc_threshold}万/ml")
            
            # 识别慢性感染牛
            chronic_mastitis_df = self.data_processor.identify_chronic_mastitis_cows(
                self.data_list,
                selected_months,
                scc_threshold,
                scc_operator
            )
            
            chronic_count = len(chronic_mastitis_df[chronic_mastitis_df['chronic_mastitis']])
            self.process_log_widget.append(f"✅ 慢性感染识别完成: {chronic_count}头牛被识别为慢性感染")
            
            # 将慢性感染结果合并到基础数据中
            if not chronic_mastitis_df.empty:
                # 确定合并字段
                cattle_info_columns = processed_data['cattle_info'].columns
                chronic_columns = chronic_mastitis_df.columns
                
                if 'management_id' in cattle_info_columns and 'management_id' in chronic_columns:
                    merge_key = 'management_id'
                elif 'ear_tag' in cattle_info_columns and 'ear_tag' in chronic_columns:
                    merge_key = 'ear_tag'
                else:
                    # 如果没有直接匹配的字段，尝试创建匹配字段
                    if 'ear_tag' in cattle_info_columns and 'management_id' in chronic_columns:
                        # 牛群信息用ear_tag，慢性感染结果用management_id，尝试匹配
                        merge_key = 'ear_tag'  # 使用ear_tag作为主键
                        chronic_mastitis_df['ear_tag'] = chronic_mastitis_df['management_id']
                    else:
                        self.process_log_widget.append("❌ 无法找到合适的字段合并慢性感染结果")
                        processed_data['cattle_info']['chronic_mastitis'] = False
                        merge_key = None
                
                if merge_key:
                    processed_data['cattle_info'] = processed_data['cattle_info'].merge(
                        chronic_mastitis_df, 
                        left_on=merge_key, 
                        right_on=merge_key, 
                        how='left'
                    )
                    # 填充缺失值为False（非慢性感染）
                    processed_data['cattle_info']['chronic_mastitis'] = processed_data['cattle_info']['chronic_mastitis'].fillna(False)
                    self.process_log_widget.append(f"✅ 慢性感染结果已使用{merge_key}字段合并到基础数据中")
            else:
                # 如果没有慢性感染牛，所有牛的chronic_mastitis都设为False
                processed_data['cattle_info']['chronic_mastitis'] = False
                self.process_log_widget.append("ℹ️ 未发现慢性感染牛，所有牛的chronic_mastitis设为False")
            
            self.mastitis_progress_dialog.setValue(85)
            self.mastitis_progress_dialog.setLabelText("步骤 7/8: 应用处置办法...")
            self.process_log_widget.append("⚖️ 应用处置办法判断...")
            QApplication.processEvents()
            
            # 收集处置办法配置
            treatment_config = self.build_treatment_config()
            enabled_treatments = [k for k, v in treatment_config.items() if v.get('enabled', False)]
            self.process_log_widget.append(f"📋 启用的处置办法: {', '.join(enabled_treatments)}")
            
            # 应用处置办法判断（只对慢性感染牛进行判断）
            final_results = self.data_processor.apply_treatment_decisions(
                processed_data['cattle_info'], treatment_config
            )
            
            self.mastitis_progress_dialog.setValue(95)
            self.mastitis_progress_dialog.setLabelText("步骤 8/8: 生成筛查报告...")
            self.process_log_widget.append("📊 生成筛查报告...")
            QApplication.processEvents()
            
            # 生成筛查报告
            screening_report = self.data_processor.create_mastitis_screening_report(
                final_results, 
                selected_months, 
                self.data_list
            )
            
            self.mastitis_progress_dialog.setValue(100)
            self.mastitis_progress_dialog.setLabelText("筛查完成！")
            # 延迟关闭进度对话框
            QTimer.singleShot(2000, lambda: self.mastitis_progress_dialog.close())
            
            completion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if not screening_report.empty:
                self.mastitis_screening_results = screening_report
                self.mastitis_export_btn.setEnabled(True)
                result_message = f"✅ 筛查完成！发现{len(screening_report)}头牛需要处置"
                self.mastitis_status_label.setText(result_message)
                
                self.process_log_widget.append(f"""
{result_message}
📅 完成时间: {completion_time}
📊 筛查结果已显示在右侧"筛选结果"标签页

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 慢性乳房炎筛查任务完成
""")
                
                # 显示结果到右侧筛选结果表格
                self.display_mastitis_results_in_table(screening_report)
            else:
                no_result_message = "✅ 筛查完成，未发现需要处置的牛只"
                self.mastitis_status_label.setText(no_result_message)
                self.process_log_widget.append(f"""
{no_result_message}
📅 完成时间: {completion_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 慢性乳房炎筛查任务完成
""")
            
        except Exception as e:
            error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            error_message = f"""
❌ 筛查过程中出现错误
📅 错误时间: {error_time}
🔍 错误详情: {str(e)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 慢性乳房炎筛查任务失败
"""
            self.process_log_widget.append(error_message)
            self.mastitis_progress_dialog.close()
            QMessageBox.critical(self, "筛查失败", f"筛查过程中出现错误：{str(e)}")
            self.mastitis_status_label.setText("筛查失败")
    
    def display_mastitis_results_in_table(self, results_df):
        """将慢性乳房炎筛查结果显示到慢性乳房炎筛查结果表格"""
        try:
            # 切换到筛选结果标签页，然后切换到慢性乳房炎筛查子标签页
            self.tab_widget.setCurrentWidget(self.result_widget)
            # 切换到慢性乳房炎筛查子标签页
            for i in range(self.result_sub_tabs.count()):
                if "慢性乳房炎筛查" in self.result_sub_tabs.tabText(i):
                    self.result_sub_tabs.setCurrentIndex(i)
                    break
            
            # 设置表格行列数
            self.mastitis_screening_table.setRowCount(len(results_df))
            self.mastitis_screening_table.setColumnCount(len(results_df.columns))
            
            # 设置表头
            self.mastitis_screening_table.setHorizontalHeaderLabels(results_df.columns.tolist())
            
            # 填充数据
            for i in range(len(results_df)):
                for j, value in enumerate(results_df.iloc[i]):
                    item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                    
                    # 为不同的处置办法设置不同的背景色
                    if j == results_df.columns.get_loc('推荐处置办法') if '推荐处置办法' in results_df.columns else -1:
                        if '淘汰' in str(value):
                            item.setBackground(QColor(255, 235, 238))  # 淡红色
                        elif '禁配隔离' in str(value):
                            item.setBackground(QColor(255, 243, 205))  # 淡橙色
                        elif '瞎乳区' in str(value):
                            item.setBackground(QColor(217, 237, 247))  # 淡蓝色
                        elif '提前干奶' in str(value):
                            item.setBackground(QColor(230, 247, 236))  # 淡绿色
                        elif '治疗' in str(value):
                            item.setBackground(QColor(248, 249, 250))  # 淡灰色
                    
                    self.mastitis_screening_table.setItem(i, j, item)
            
            # 调整列宽
            self.mastitis_screening_table.resizeColumnsToContents()
            
            # 限制列宽最大值
            for col in range(self.mastitis_screening_table.columnCount()):
                if self.mastitis_screening_table.columnWidth(col) > 200:
                    self.mastitis_screening_table.setColumnWidth(col, 200)
            
            # 启用排序
            self.mastitis_screening_table.setSortingEnabled(True)
            
            # 在处理过程中添加结果说明
            result_summary = f"""
📊 结果已显示在慢性乳房炎筛查结果表格中
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 筛查结果摘要:
• 总计: {len(results_df)} 头牛需要处置
• 数据列: {len(results_df.columns)} 个字段
• 表格支持点击列头排序

💡 处置办法颜色说明:
🔴 淘汰 - 淡红色背景
🟠 禁配隔离 - 淡橙色背景  
🔵 瞎乳区 - 淡蓝色背景
🟢 提前干奶 - 淡绿色背景
⚪ 治疗 - 淡灰色背景

📍 查看结果：点击右侧"筛查结果"标签页中的"慢性乳房炎筛查"子标签
"""
            self.process_log_widget.append(result_summary)
            
        except Exception as e:
            error_msg = f"❌ 显示筛查结果时出错: {str(e)}"
            self.process_log_widget.append(error_msg)
            print(f"显示筛查结果时出错: {e}")
    
    def build_treatment_config(self) -> Dict[str, Any]:
        """构建处置办法配置"""
        config = {}

        for method_key, widget in self.treatment_configs.items():
            if widget.enabled_cb.isChecked():
                method_config = {
                    'enabled': True,
                    'mastitis_operator': widget.mastitis_combo.currentText(),
                    'mastitis_value': widget.mastitis_spin.value(),
                    'lactation_operator': widget.lactation_combo.currentText(),
                    'lactation_value': widget.lactation_spin.value(),
                    'breeding_status': [status for status, cb in widget.breeding_checkboxes.items() if cb.isChecked()]
                }

                # 添加产奶量配置（淘汰、禁配隔离、瞎乳区、提前干奶、治疗都有）
                if hasattr(widget, 'yield_combo'):
                    method_config['yield_operator'] = widget.yield_combo.currentText()
                    method_config['yield_value'] = widget.yield_spin.value()

                # 添加在胎天数配置（瞎乳区、提前干奶、治疗有）
                if hasattr(widget, 'gestation_combo'):
                    method_config['gestation_operator'] = widget.gestation_combo.currentText()
                    method_config['gestation_value'] = widget.gestation_spin.value()

                config[method_key] = method_config
            else:
                config[method_key] = {'enabled': False}

        return config
    
    def show_mastitis_results_preview(self, results_df):
        """显示筛查结果预览"""
        if results_df.empty:
            return
        
        # 创建预览对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("慢性乳房炎筛查结果预览")
        dialog.resize(1000, 600)
        
        layout = QVBoxLayout(dialog)
        
        # 统计信息
        stats_label = QLabel(f"共发现 {len(results_df)} 头牛需要处置")
        stats_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        layout.addWidget(stats_label)
        
        # 结果表格
        table = QTableWidget()
        table.setRowCount(min(len(results_df), 100))  # 最多显示100行
        table.setColumnCount(len(results_df.columns))
        table.setHorizontalHeaderLabels(results_df.columns.tolist())
        
        # 填充数据
        for i in range(min(len(results_df), 100)):
            for j, value in enumerate(results_df.iloc[i]):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                table.setItem(i, j, item)
        
        # 自适应列宽
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        # 按钮
        button_layout = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        export_btn = QPushButton("导出完整结果")
        export_btn.clicked.connect(lambda: [dialog.accept(), self.export_mastitis_results()])
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addWidget(export_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def export_mastitis_results(self):
        """导出慢性乳房炎筛查结果"""
        if self.mastitis_screening_results is None or self.mastitis_screening_results.empty:
            QMessageBox.warning(self, "导出失败", "没有筛查结果可以导出")
            return
        
        # 选择保存路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"慢性乳房炎筛查结果_{timestamp}.xlsx"
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "保存筛查结果", default_filename, 
            "Excel文件 (*.xlsx);;所有文件 (*)"
        )
        
        if file_path:
            try:
                success = self.data_processor.export_mastitis_screening_results(
                    self.mastitis_screening_results, file_path
                )
                
                if success:
                    self.show_export_success_dialog("筛查结果已保存到：", file_path)
                else:
                    QMessageBox.warning(self, "导出失败", "导出过程中出现错误")
                    
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出时出现错误：{str(e)}")

    def show_export_success_dialog(self, message: str, file_path: str):
        """显示导出成功对话框，包含打开文件和打开文件夹按钮"""
        dialog = QDialog(self)
        dialog.setWindowTitle("导出成功")
        dialog.setFixedSize(500, 200)
        dialog.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        
        # 主布局
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 成功图标和消息
        message_layout = QHBoxLayout()
        
        # 成功图标
        icon_label = QLabel()
        icon_pixmap = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation).pixmap(48, 48)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 消息文本
        message_label = QLabel(f"{message}\n{file_path}")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        message_label.setStyleSheet("font-size: 14px; color: #333333;")
        
        message_layout.addWidget(icon_label)
        message_layout.addWidget(message_label)
        message_layout.addStretch()
        
        layout.addLayout(message_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 打开文件按钮
        open_file_btn = QPushButton("📄 打开文件")
        open_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        open_file_btn.clicked.connect(lambda: self.open_file(file_path))
        
        # 打开文件夹按钮
        open_folder_btn = QPushButton("📁 打开文件夹")
        open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        open_folder_btn.clicked.connect(lambda: self.open_file_folder(file_path))
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        
        # 添加按钮到布局
        button_layout.addWidget(open_file_btn)
        button_layout.addWidget(open_folder_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # 设置对话框样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QLabel {
                background-color: transparent;
            }
        """)
        
        # 显示对话框
        dialog.exec()
    
    def start_mastitis_monitoring(self):
        """启动隐形乳房炎月度监测分析"""
        try:
            print(f"\n🔍 [详细调试] 开始隐形乳房炎监测分析...")
            
            # 详细检查系统状态
            print(f"🔍 [详细调试] 检查DHI数据可用性...")
            print(f"   hasattr(self, 'data_list'): {hasattr(self, 'data_list')}")
            if hasattr(self, 'data_list'):
                print(f"   self.data_list is not None: {self.data_list is not None}")
                if self.data_list:
                    print(f"   DHI数据文件数量: {len(self.data_list)}")
                    for i, item in enumerate(self.data_list):
                        print(f"     文件{i+1}: {item.get('filename', 'Unknown')} - 数据行数: {len(item['data']) if item.get('data') is not None else 0}")
            
            print(f"🔍 [详细调试] 检查牛群基础信息...")
            print(f"   hasattr(self, 'cattle_basic_info'): {hasattr(self, 'cattle_basic_info')}")
            if hasattr(self, 'cattle_basic_info'):
                print(f"   self.cattle_basic_info is not None: {self.cattle_basic_info is not None}")
                if self.cattle_basic_info is not None:
                    print(f"   牛群基础信息数量: {len(self.cattle_basic_info)}")
                    print(f"   牛群数据列名: {list(self.cattle_basic_info.columns)}")
                    print(f"   系统类型: {getattr(self, 'current_system', 'Unknown')}")
                    # 显示前几头牛的信息
                    if len(self.cattle_basic_info) > 0:
                        print(f"   前3头牛示例:")
                        for i in range(min(3, len(self.cattle_basic_info))):
                            cow_data = self.cattle_basic_info.iloc[i]
                            print(f"     牛{i+1}: 耳号={cow_data.get('ear_tag', 'N/A')}, 在胎天数={cow_data.get('gestation_days', 'N/A')}")
            
            print(f"🔍 [详细调试] 检查监测计算器...")
            print(f"   hasattr(self, 'mastitis_monitoring_calculator'): {hasattr(self, 'mastitis_monitoring_calculator')}")
            if hasattr(self, 'mastitis_monitoring_calculator'):
                print(f"   计算器对象: {self.mastitis_monitoring_calculator}")
                if self.mastitis_monitoring_calculator:
                    print(f"   计算器中是否有牛群数据: {hasattr(self.mastitis_monitoring_calculator, 'cattle_basic_info')}")
                    if hasattr(self.mastitis_monitoring_calculator, 'cattle_basic_info'):
                        print(f"   计算器中牛群数据: {self.mastitis_monitoring_calculator.cattle_basic_info is not None}")
            
            # 检查DHI数据是否可用
            if not hasattr(self, 'data_list') or not self.data_list:
                self.show_warning("警告", "请先在'DHI基础筛选'标签页中上传DHI数据")
                return
            
            # 获取阈值设置
            scc_threshold = self.monitoring_scc_threshold.value()
            
            # 从监测计算模块导入
            from mastitis_monitoring import MastitisMonitoringCalculator
            
            # 创建监测计算器
            self.mastitis_monitoring_calculator = MastitisMonitoringCalculator(scc_threshold=scc_threshold)
            
            # 准备DHI数据
            dhi_data_list = []
            for item in self.data_list:
                if item['data'] is not None and not item['data'].empty:
                    dhi_data_list.append(item['data'])
            
            if len(dhi_data_list) == 0:
                QMessageBox.warning(self, "警告", "没有可用的DHI数据进行分析")
                return
            
            # 加载DHI数据
            load_result = self.mastitis_monitoring_calculator.load_dhi_data(dhi_data_list)
            
            if not load_result['success']:
                QMessageBox.critical(self, "错误", f"DHI数据加载失败: {load_result.get('error', '未知错误')}")
                return
            
            # 自动加载慢性乳房炎筛查中的牛群基础信息
            print(f"\n🔍 检查牛群基础信息...")
            print(f"   hasattr(self, 'cattle_basic_info'): {hasattr(self, 'cattle_basic_info')}")
            if hasattr(self, 'cattle_basic_info'):
                print(f"   self.cattle_basic_info is not None: {self.cattle_basic_info is not None}")
                if self.cattle_basic_info is not None:
                    print(f"   牛群基础信息数量: {len(self.cattle_basic_info)}")
                    print(f"   系统类型: {getattr(self, 'current_system', 'Unknown')}")
            
            if hasattr(self, 'cattle_basic_info') and self.cattle_basic_info is not None:
                print(f"   ✅ 发现慢性乳房炎筛查中的牛群数据，自动加载到监测计算器...")
                print(f"   牛群数据详情: {len(self.cattle_basic_info)}头牛, 系统类型: {getattr(self, 'current_system', 'Unknown')}")
                print(f"   牛群数据列: {list(self.cattle_basic_info.columns)}")
                
                cattle_result = self.mastitis_monitoring_calculator.load_cattle_basic_info(
                    self.cattle_basic_info, self.current_system)
                    
                print(f"   加载结果: {cattle_result}")
                
                if not cattle_result['success']:
                    print(f"   ❌ 牛群基础信息加载失败: {cattle_result.get('error')}")
                    self.show_warning("提示", f"牛群基础信息加载失败: {cattle_result.get('error', '未知错误')}\n将无法计算干奶前流行率")
                else:
                    print(f"   ✅ 牛群基础信息加载成功，可计算干奶前流行率")
                    print(f"   加载详情: {cattle_result.get('message', '无详情')}")
                    # 更新状态显示
                    self.update_monitoring_data_status()
            else:
                print(f"   ❌ 跳过牛群基础信息加载：数据不存在")
                print(f"   💡 提示：如需计算干奶前流行率，请先到'慢性乳房炎筛查'中上传牛群基础信息")
            
            # 定义异步计算任务
            def calculate_task(progress_callback=None, status_callback=None, check_cancelled=None):
                if status_callback:
                    status_callback("正在计算各项指标...")
                
                if progress_callback:
                    progress_callback(30)
                
                results = self.mastitis_monitoring_calculator.calculate_all_indicators()
                
                if progress_callback:
                    progress_callback(100)
                    
                return results
            
            # 执行计算
            self.start_monitoring_btn.setText("计算中...")
            self.start_monitoring_btn.setEnabled(False)
            
            # 使用异步进度管理器执行计算
            progress_manager = AsyncProgressManager(self)
            results = progress_manager.execute_with_progress(
                calculate_task,
                title="隐性乳房炎监测分析",
                cancel_text="取消",
                total_steps=100
            )
            
            if not results['success']:
                QMessageBox.critical(self, "错误", f"指标计算失败: {results.get('error', '未知错误')}")
                self.start_monitoring_btn.setText("开始分析")
                self.start_monitoring_btn.setEnabled(True)
                return
            
            # 保存结果
            self.mastitis_monitoring_results = results
            
            # 显示结果
            self.display_mastitis_monitoring_results(results)
            
            # 启用导出按钮
            self.export_monitoring_btn.setEnabled(True)
            
            # 重置按钮
            self.start_monitoring_btn.setText("重新分析")
            self.start_monitoring_btn.setEnabled(True)
            
            QMessageBox.information(self, "完成", f"隐形乳房炎监测分析完成！\n分析了{results['month_count']}个月份的数据")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析过程中发生错误: {str(e)}")
            logger.error(f"隐形乳房炎监测分析失败: {e}")
            self.start_monitoring_btn.setText("开始分析")
            self.start_monitoring_btn.setEnabled(True)
    
    def display_mastitis_monitoring_results(self, results):
        """显示隐形乳房炎监测结果"""
        try:
            # 更新表格
            self.update_monitoring_table(results)
            
            # 更新图表
            self.update_monitoring_chart(results)
            
        except Exception as e:
            logger.error(f"显示监测结果失败: {e}")
            QMessageBox.warning(self, "警告", f"显示结果失败: {str(e)}")
    
    def update_monitoring_table(self, results):
        """更新监测结果表格"""
        try:
            months = results['months']
            indicators = results['indicators']
            
            # 定义表格列
            columns = [
                '月份', '当月流行率(%)', '新发感染率(%)', '慢性感染率(%)', 
                '慢性感染牛占比(%)', '头胎首测流行率(%)', '经产首测流行率(%)', '干奶前流行率(%)'
            ]
            
            self.mastitis_monitoring_table.setColumnCount(len(columns))
            self.mastitis_monitoring_table.setHorizontalHeaderLabels(columns)
            self.mastitis_monitoring_table.setRowCount(len(months))
            
            for row, month in enumerate(months):
                month_data = indicators.get(month, {})
                
                # 月份
                self.mastitis_monitoring_table.setItem(row, 0, QTableWidgetItem(month))
                
                # 当月流行率
                cp = month_data.get('current_prevalence', {})
                cp_value = f"{cp['value']:.1f}" if cp.get('value') is not None else "N/A"
                cp_item = QTableWidgetItem(cp_value)
                if cp.get('value') is not None:
                    cp_item.setToolTip(cp.get('formula', ''))
                self.mastitis_monitoring_table.setItem(row, 1, cp_item)
                
                # 新发感染率
                nir = month_data.get('new_infection_rate', {})
                nir_value = f"{nir['value']:.1f}" if nir.get('value') is not None else "N/A"
                nir_item = QTableWidgetItem(nir_value)
                if nir.get('value') is not None:
                    tooltip = nir.get('formula', '')
                    if nir.get('warning'):
                        tooltip += f"\n⚠️ {nir['warning']}"
                    nir_item.setToolTip(tooltip)
                self.mastitis_monitoring_table.setItem(row, 2, nir_item)
                
                # 慢性感染率
                cir = month_data.get('chronic_infection_rate', {})
                cir_value = f"{cir['value']:.1f}" if cir.get('value') is not None else "N/A"
                cir_item = QTableWidgetItem(cir_value)
                if cir.get('value') is not None:
                    tooltip = cir.get('formula', '')
                    if cir.get('warning'):
                        tooltip += f"\n⚠️ {cir['warning']}"
                    cir_item.setToolTip(tooltip)
                self.mastitis_monitoring_table.setItem(row, 3, cir_item)
                
                # 慢性感染牛占比
                cip = month_data.get('chronic_infection_proportion', {})
                cip_value = f"{cip['value']:.1f}" if cip.get('value') is not None else "N/A"
                cip_item = QTableWidgetItem(cip_value)
                if cip.get('value') is not None:
                    tooltip = cip.get('formula', '')
                    if cip.get('warning'):
                        tooltip += f"\n⚠️ {cip['warning']}"
                    cip_item.setToolTip(tooltip)
                self.mastitis_monitoring_table.setItem(row, 4, cip_item)
                
                # 头胎首测流行率
                ftp = month_data.get('first_test_prevalence', {})
                primi_value = "N/A"
                if ftp and 'primiparous' in ftp:
                    primi_data = ftp['primiparous']
                    primi_value = f"{primi_data['value']:.1f}" if primi_data.get('value') is not None else "N/A"
                primi_item = QTableWidgetItem(primi_value)
                if ftp and 'primiparous' in ftp:
                    primi_item.setToolTip(ftp['primiparous'].get('formula', ''))
                self.mastitis_monitoring_table.setItem(row, 5, primi_item)
                
                # 经产首测流行率
                multi_value = "N/A"
                if ftp and 'multiparous' in ftp:
                    multi_data = ftp['multiparous']
                    multi_value = f"{multi_data['value']:.1f}" if multi_data.get('value') is not None else "N/A"
                multi_item = QTableWidgetItem(multi_value)
                if ftp and 'multiparous' in ftp:
                    multi_item.setToolTip(ftp['multiparous'].get('formula', ''))
                self.mastitis_monitoring_table.setItem(row, 6, multi_item)
                
                # 干奶前流行率（只在最新月份显示）
                pdp = month_data.get('pre_dry_prevalence', {})
                is_latest_month = (row == len(months) - 1)  # 判断是否为最新月份
                
                # 调试输出
                print(f"🔍 干奶前流行率调试 - 月份: {month}")
                print(f"   是否最新月份: {is_latest_month}")
                print(f"   干奶前流行率数据: {pdp}")
                print(f"   数值: {pdp.get('value')}")
                print(f"   诊断: {pdp.get('diagnosis')}")
                
                if is_latest_month and pdp.get('value') is not None:
                    # 最新月份且有数值
                    pdp_value = f"{pdp['value']:.1f}"
                    pdp_item = QTableWidgetItem(pdp_value)
                    
                    # 设置详细的工具提示，包含诊断信息
                    if pdp.get('formula'):
                        # 将HTML标签转换为纯文本用于工具提示
                        tooltip_text = pdp.get('formula', '').replace('<br/>', '\n').replace('　', '  ')
                        # 移除HTML标签
                        import re
                        tooltip_text = re.sub(r'<[^>]+>', '', tooltip_text)
                        pdp_item.setToolTip(tooltip_text)
                    
                    # 设置成功计算的颜色
                    pdp_item.setBackground(QColor('#e8f5e8'))  # 浅绿色
                    
                elif is_latest_month and pdp.get('formula'):
                    # 最新月份但计算失败，显示具体错误
                    print(f"   💡 干奶前流行率计算失败，显示N/A")
                    pdp_value = "N/A"
                    pdp_item = QTableWidgetItem(pdp_value)
                    
                    # 设置详细的工具提示，包含诊断信息
                    tooltip_text = pdp.get('formula', '').replace('<br/>', '\n').replace('　', '  ')
                    # 移除HTML标签
                    import re
                    tooltip_text = re.sub(r'<[^>]+>', '', tooltip_text)
                    pdp_item.setToolTip(tooltip_text)
                    
                    # 根据诊断结果设置不同的颜色
                    diagnosis = pdp.get('diagnosis', '')
                    if diagnosis in ['缺少牛群基础信息', '数据无法匹配']:
                        pdp_item.setBackground(QColor('#ffebee'))  # 浅红色
                        pdp_item.setForeground(QColor('black'))  # 黑色字体
                    elif diagnosis in ['缺少在胎天数字段', '匹配牛只无在胎天数数据', '无符合干奶前条件的牛只']:
                        pdp_item.setBackground(QColor('#fff3e0'))  # 浅橙色
                        pdp_item.setForeground(QColor('black'))  # 黑色字体
                else:
                    # 非最新月份，显示"-"
                    print(f"   💡 显示'-'，原因: 非最新月份或无数据")
                    pdp_value = "-"
                    pdp_item = QTableWidgetItem(pdp_value)
                    pdp_item.setToolTip("干奶前流行率只在最新月份计算")
                    pdp_item.setForeground(QColor('black'))  # 黑色字体
                
                self.mastitis_monitoring_table.setItem(row, 7, pdp_item)
            
            # 调整列宽
            self.mastitis_monitoring_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"更新监测表格失败: {e}")
            raise
    
    def update_monitoring_chart(self, results):
        """更新监测趋势图表"""
        try:
            import pyqtgraph as pg
            
            # 清除现有图表
            self.mastitis_monitoring_plot.clear()
            
            months = results['months']
            indicators = results['indicators']
            
            if len(months) == 0:
                return
            
            # 准备数据
            x_values = list(range(len(months)))
            x_labels = months
            
            # 定义线条样式
            line_styles = [
                {'color': '#e74c3c', 'width': 2, 'style': None},  # 当月流行率 - 红色
                {'color': '#f39c12', 'width': 2, 'style': None},  # 新发感染率 - 橙色  
                {'color': '#9b59b6', 'width': 2, 'style': None},  # 慢性感染率 - 紫色
                {'color': '#3498db', 'width': 2, 'style': None},  # 慢性感染牛占比 - 蓝色
                {'color': '#27ae60', 'width': 2, 'style': None},  # 首测流行率 - 绿色
            ]
            
            line_index = 0
            
            # 绘制各指标线条（默认显示所有指标）
            # 1. 当月流行率
            y_values = []
            for month in months:
                cp = indicators[month].get('current_prevalence', {})
                y_values.append(cp.get('value', None))
            
            valid_points = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
            if valid_points:
                x_valid, y_valid = zip(*valid_points)
                self.mastitis_monitoring_plot.plot(
                    x_valid, y_valid, 
                    pen=pg.mkPen(color=line_styles[line_index]['color'], width=line_styles[line_index]['width']),
                    symbol='o', symbolSize=8, symbolBrush=line_styles[line_index]['color'],
                    name='当月流行率'
                )
            line_index += 1
            
            # 2. 新发感染率
            y_values = []
            for month in months:
                nir = indicators[month].get('new_infection_rate', {})
                y_values.append(nir.get('value', None))
            
            valid_points = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
            if valid_points:
                x_valid, y_valid = zip(*valid_points)
                self.mastitis_monitoring_plot.plot(
                    x_valid, y_valid,
                    pen=pg.mkPen(color=line_styles[line_index]['color'], width=line_styles[line_index]['width']),
                    symbol='s', symbolSize=8, symbolBrush=line_styles[line_index]['color'],
                    name='新发感染率'
                )
            line_index += 1
            
            # 3. 慢性感染率
            y_values = []
            for month in months:
                cir = indicators[month].get('chronic_infection_rate', {})
                y_values.append(cir.get('value', None))
            
            valid_points = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
            if valid_points:
                x_valid, y_valid = zip(*valid_points)
                self.mastitis_monitoring_plot.plot(
                    x_valid, y_valid,
                    pen=pg.mkPen(color=line_styles[line_index]['color'], width=line_styles[line_index]['width']),
                    symbol='t', symbolSize=8, symbolBrush=line_styles[line_index]['color'],
                    name='慢性感染率'
                )
            line_index += 1
            
            # 4. 慢性感染牛占比
            y_values = []
            for month in months:
                cip = indicators[month].get('chronic_infection_proportion', {})
                y_values.append(cip.get('value', None))
            
            valid_points = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
            if valid_points:
                x_valid, y_valid = zip(*valid_points)
                self.mastitis_monitoring_plot.plot(
                    x_valid, y_valid,
                    pen=pg.mkPen(color=line_styles[line_index]['color'], width=line_styles[line_index]['width']),
                    symbol='d', symbolSize=8, symbolBrush=line_styles[line_index]['color'],
                    name='慢性感染牛占比'
                )
            line_index += 1
            
            # 5. 首测流行率（头胎）
            y_values = []
            for month in months:
                ftp = indicators[month].get('first_test_prevalence', {})
                if ftp and 'primiparous' in ftp:
                    y_values.append(ftp['primiparous'].get('value', None))
                else:
                    y_values.append(None)
            
            valid_points = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
            if valid_points:
                x_valid, y_valid = zip(*valid_points)
                self.mastitis_monitoring_plot.plot(
                    x_valid, y_valid,
                    pen=pg.mkPen(color=line_styles[line_index]['color'], width=line_styles[line_index]['width'], style=pg.QtCore.Qt.PenStyle.DashLine),
                    symbol='+', symbolSize=10, symbolBrush=line_styles[line_index]['color'],
                    name='头胎首测流行率'
                )
            
            # 设置X轴标签
            x_axis = self.mastitis_monitoring_plot.getAxis('bottom')
            x_axis.setTicks([[(i, month) for i, month in enumerate(months)]])
            
            # 设置Y轴范围
            self.mastitis_monitoring_plot.setYRange(0, 100)
            
        except Exception as e:
            logger.error(f"更新监测图表失败: {e}")
            raise
    
    def export_monitoring_results(self):
        """导出隐形乳房炎监测结果到Excel"""
        try:
            if not self.mastitis_monitoring_results:
                QMessageBox.warning(self, "警告", "没有可导出的监测结果")
                return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出监测结果", 
                f"隐形乳房炎监测结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel文件 (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # 准备导出数据
            results = self.mastitis_monitoring_results
            months = results['months']
            indicators = results['indicators']
            
            # 创建DataFrame
            export_data = []
            for month in months:
                month_data = indicators.get(month, {})
                
                row = {
                    '月份': month,
                    '当月流行率(%)': self._get_indicator_value(month_data, 'current_prevalence'),
                    '当月流行率_公式': self._get_indicator_formula(month_data, 'current_prevalence'),
                    '新发感染率(%)': self._get_indicator_value(month_data, 'new_infection_rate'),
                    '新发感染率_公式': self._get_indicator_formula(month_data, 'new_infection_rate'),
                    '慢性感染率(%)': self._get_indicator_value(month_data, 'chronic_infection_rate'),
                    '慢性感染率_公式': self._get_indicator_formula(month_data, 'chronic_infection_rate'),
                    '慢性感染牛占比(%)': self._get_indicator_value(month_data, 'chronic_infection_proportion'),
                    '慢性感染牛占比_公式': self._get_indicator_formula(month_data, 'chronic_infection_proportion'),
                    '头胎首测流行率(%)': self._get_first_test_value(month_data, 'primiparous'),
                    '头胎首测流行率_公式': self._get_first_test_formula(month_data, 'primiparous'),
                    '经产首测流行率(%)': self._get_first_test_value(month_data, 'multiparous'),
                    '经产首测流行率_公式': self._get_first_test_formula(month_data, 'multiparous'),
                    '干奶前流行率(%)': self._get_indicator_value(month_data, 'pre_dry_prevalence'),
                    '干奶前流行率_公式': self._get_indicator_formula(month_data, 'pre_dry_prevalence'),
                }
                export_data.append(row)
            
            df = pd.DataFrame(export_data)
            
            # 保存到Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='监测结果', index=False)
                
                # 添加汇总信息sheet
                summary_data = {
                    '项目': ['分析日期', '体细胞阈值', '分析月份数', '日期范围', '月份连续性'],
                    '值': [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        f"{results['scc_threshold']}万/ml",
                        results['month_count'],
                        f"{months[0]} 至 {months[-1]}" if months else "无",
                        "连续" if results['continuity_check']['is_continuous'] else f"不连续，缺失：{', '.join(results['continuity_check']['missing_months'])}"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='分析汇总', index=False)
            
            self.show_export_success_dialog(f"隐形乳房炎监测结果已成功导出！", file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
            logger.error(f"导出监测结果失败: {e}")
    
    def _get_indicator_value(self, month_data, indicator_name):
        """获取指标数值"""
        indicator = month_data.get(indicator_name, {})
        value = indicator.get('value')
        return f"{value:.1f}" if value is not None else "N/A"
    
    def _get_indicator_formula(self, month_data, indicator_name):
        """获取指标公式"""
        indicator = month_data.get(indicator_name, {})
        return indicator.get('formula', '')
    
    def _get_first_test_value(self, month_data, test_type):
        """获取首测流行率数值"""
        ftp = month_data.get('first_test_prevalence', {})
        if ftp and test_type in ftp:
            value = ftp[test_type].get('value')
            return f"{value:.1f}" if value is not None else "N/A"
        return "N/A"
    
    def _get_first_test_formula(self, month_data, test_type):
        """获取首测流行率公式"""
        ftp = month_data.get('first_test_prevalence', {})
        if ftp and test_type in ftp:
            return ftp[test_type].get('formula', '')
        return ""
    
    def toggle_monitoring_formula_visibility(self):
        """切换隐形乳房炎监测公式说明的显示/隐藏状态"""
        if self.monitoring_formula_widget.isVisible():
            self.monitoring_formula_widget.setVisible(False)
            self.formula_toggle_btn.setText("▼ 展开公式详情")
        else:
            self.monitoring_formula_widget.setVisible(True)
            self.formula_toggle_btn.setText("▲ 收起公式详情")
    
    def update_monitoring_threshold(self):
        """更新隐形乳房炎监测的体细胞阈值"""
        if hasattr(self, 'mastitis_monitoring_calculator') and self.mastitis_monitoring_calculator:
            new_threshold = self.monitoring_scc_threshold.value()
            self.mastitis_monitoring_calculator.set_scc_threshold(new_threshold)
            logger.info(f"体细胞阈值已更新为: {new_threshold} 万/ml")
    
    def update_monitoring_display(self):
        """更新隐形乳房炎监测显示（重新计算并显示结果）"""
        if hasattr(self, 'mastitis_monitoring_results') and self.mastitis_monitoring_results:
            # 重新计算指标
            results = self.mastitis_monitoring_calculator.calculate_all_indicators()
            if results['success']:
                self.mastitis_monitoring_results = results
                self.display_mastitis_monitoring_results(results)
            else:
                QMessageBox.warning(self, "更新失败", f"重新计算失败: {results.get('error', '未知错误')}")
    
    def upload_dhi_for_monitoring(self):
        """为隐形乳房炎监测上传DHI数据"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择DHI报告文件（隐形乳房炎监测）",
            "",
            "支持的文件 (*.zip *.xlsx *.xls);;ZIP文件 (*.zip);;Excel文件 (*.xlsx *.xls)"
        )
        
        if not files:
            return
        
        try:
            # 使用新的流畅进度条
            progress_dialog = SmoothProgressDialog("正在处理DHI文件...", "取消", 0, len(files), self)
            progress_dialog.show()
            
            # 处理DHI文件
            from data_processor import DataProcessor
            processor = DataProcessor()
            
            all_dhi_data = []
            success_files = []
            failed_files = []
            
            for i, file_path in enumerate(files):
                if progress_dialog.wasCanceled():
                    break
                
                filename = os.path.basename(file_path)
                progress_dialog.setLabelText(f"处理: {filename}")
                progress_dialog.setValue(i)
                QApplication.processEvents()
                
                try:
                    # 处理单个DHI文件
                    success, message, df = processor.process_file(file_path, filename)
                    
                    if success and df is not None and not df.empty:
                        all_dhi_data.append(df)
                        success_files.append(filename)
                    else:
                        failed_files.append(f"{filename}: {message}")
                        
                except Exception as e:
                    failed_files.append(f"{filename}: {str(e)}")
            
            progress_dialog.setValue(len(files))
            progress_dialog.close()
            
            if all_dhi_data:
                # 初始化监测计算器
                try:
                    from mastitis_monitoring import MastitisMonitoringCalculator
                    
                    if not hasattr(self, 'mastitis_monitoring_calculator'):
                        self.mastitis_monitoring_calculator = MastitisMonitoringCalculator()
                    
                    # 加载DHI数据
                    load_result = self.mastitis_monitoring_calculator.load_dhi_data(all_dhi_data)
                    
                    if load_result['success']:
                        # 更新监测状态显示
                        self.update_monitoring_data_status()
                        
                        # 更新状态信息
                        self.monitoring_status_label.setText(f"✅ DHI数据已上传，包含 {load_result['month_count']} 个月份的数据")
                        
                        QMessageBox.information(
                            self, 
                            "上传成功", 
                            f"DHI数据上传成功！\n\n"
                            f"成功处理: {len(success_files)} 个文件\n"
                            f"数据月份: {load_result['month_count']} 个月\n"
                            f"时间范围: {load_result['date_range']['start']} - {load_result['date_range']['end']}"
                        )
                        
                    else:
                        QMessageBox.warning(self, "加载失败", f"DHI数据加载失败: {load_result.get('error', '未知错误')}")
                        
                except ImportError:
                    QMessageBox.critical(self, "模块缺失", "缺少隐形乳房炎监测模块，请检查安装。")
                except Exception as e:
                    QMessageBox.critical(self, "处理失败", f"DHI数据处理失败: {str(e)}")
                    
            else:
                error_msg = "没有成功处理的DHI文件。\n\n失败原因:\n" + "\n".join(failed_files[:5])
                if len(failed_files) > 5:
                    error_msg += f"\n... 还有 {len(failed_files) - 5} 个文件失败"
                QMessageBox.warning(self, "处理失败", error_msg)
                
        except Exception as e:
            QMessageBox.critical(self, "上传失败", f"DHI文件上传失败: {str(e)}")
    
    def upload_cattle_info_for_monitoring(self):
        """为隐形乳房炎监测上传牛群基础信息"""
        system_type_map = {
            "伊起牛": "yiqiniu",
            "慧牧云": "huimuyun", 
            "其他": "custom"
        }
        
        system_type = system_type_map.get(self.monitoring_system_combo.currentText(), "custom")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择牛群基础信息文件",
            "",
            "Excel文件 (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # 处理牛群基础信息文件
            from data_processor import DataProcessor
            processor = DataProcessor()
            
            if system_type == "custom":
                # 自定义系统：尝试直接读取并识别字段
                try:
                    cattle_df = pd.read_excel(file_path)
                    
                    # 灵活匹配耳号字段
                    ear_tag_field = None
                    for field in ['耳号', 'ear_tag', '牛号', 'cow_id']:
                        if field in cattle_df.columns:
                            ear_tag_field = field
                            break
                    
                    # 灵活匹配在胎天数字段
                    pregnancy_field = None
                    for field in ['在胎天数', '怀孕天数', 'gestation_days', 'pregnancy_days']:
                        if field in cattle_df.columns:
                            pregnancy_field = field
                            break
                    
                    if not ear_tag_field or not pregnancy_field:
                        missing_fields = []
                        if not ear_tag_field:
                            missing_fields.append('耳号（或ear_tag/牛号）')
                        if not pregnancy_field:
                            missing_fields.append('在胎天数（或怀孕天数/gestation_days）')
                        
                        QMessageBox.warning(
                            self,
                            "字段缺失",
                            f"牛群基础信息文件缺少必要字段：\n{', '.join(missing_fields)}\n\n"
                            f"当前文件包含字段：\n{', '.join(cattle_df.columns[:10])}..."
                        )
                        return
                    
                    # 标准化数据
                    result_df = pd.DataFrame()
                    result_df['ear_tag'] = cattle_df[ear_tag_field].astype(str).str.lstrip('0').replace('', '0')
                    result_df['gestation_days'] = pd.to_numeric(cattle_df[pregnancy_field], errors='coerce')
                    
                    # 添加其他可用字段
                    optional_fields = ['胎次', '泌乳天数', '繁育状态', '最近产犊日期']
                    for field in optional_fields:
                        if field in cattle_df.columns:
                            if field == '胎次':
                                result_df['parity'] = pd.to_numeric(cattle_df[field], errors='coerce')
                            elif field == '泌乳天数':
                                result_df['lactation_days'] = pd.to_numeric(cattle_df[field], errors='coerce')
                            elif field == '繁育状态':
                                result_df['breeding_status'] = cattle_df[field].astype(str)
                            elif field == '最近产犊日期':
                                result_df['last_calving_date'] = pd.to_datetime(cattle_df[field], errors='coerce')
                    
                    # 清理数据
                    result_df = result_df.dropna(subset=['ear_tag'])
                    result_df = result_df[result_df['ear_tag'] != 'nan']
                    
                    processed_data = {'cattle_info': result_df}
                    success = True
                    message = f"成功处理{len(result_df)}条牛群基础信息"
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "文件处理失败",
                        f"无法处理自定义格式的牛群基础信息文件：\n{str(e)}\n\n"
                        "请确保文件包含'耳号'和'在胎天数'字段（或相应的英文字段名）"
                    )
                    return
            else:
                # 使用慢性乳房炎筛查的文件处理方法
                success, message, processed_data = processor.process_mastitis_system_files(
                    system_type, 
                    {'cattle_info': file_path}
                )
            
            if success and 'cattle_info' in processed_data:
                cattle_df = processed_data['cattle_info']
                
                # 初始化监测计算器（如果还没有）
                try:
                    from mastitis_monitoring import MastitisMonitoringCalculator
                    
                    if not hasattr(self, 'mastitis_monitoring_calculator'):
                        self.mastitis_monitoring_calculator = MastitisMonitoringCalculator()
                    
                    # 加载牛群基础信息
                    load_result = self.mastitis_monitoring_calculator.load_cattle_basic_info(cattle_df, system_type)
                    
                    if load_result['success']:
                        # 同时保存到主窗口，确保其他模块也能使用
                        self.cattle_basic_info = cattle_df
                        self.current_system = system_type
                        
                        # 更新状态显示
                        status_text = f"✅ 已上传牛群基础信息\n"
                        status_text += f"📊 系统类型: {self.monitoring_system_combo.currentText()}\n"
                        status_text += f"🐄 牛只数量: {load_result['cattle_count']} 头\n"
                        if load_result.get('pregnancy_field'):
                            status_text += f"🤰 在胎天数字段: {load_result['pregnancy_field']}\n"
                        
                        # 统计在胎天数>180天的牛只
                        pregnancy_field = load_result.get('pregnancy_field')
                        if pregnancy_field and pregnancy_field in cattle_df.columns:
                            pregnancy_data = cattle_df[pregnancy_field].dropna()
                            if len(pregnancy_data) > 0:
                                over_180_count = (pregnancy_data > 180).sum()
                                status_text += f"🎯 干奶前牛只(>180天): {over_180_count} 头"
                                
                        self.cattle_info_label.setText(status_text)
                        self.cattle_info_label.setStyleSheet("color: #27ae60; font-size: 10px; padding: 5px; background-color: #f8f9fa; border: 1px solid #27ae60; border-radius: 3px;")
                        
                        # 更新分析按钮状态
                        self.check_monitoring_analysis_ready()
                        
                        QMessageBox.information(
                            self,
                            "上传成功",
                            f"🎉 牛群基础信息上传成功！\n\n"
                            f"📊 系统类型: {self.monitoring_system_combo.currentText()}\n"
                            f"🐄 数据量: {load_result['cattle_count']} 头牛\n"
                            f"🤰 在胎天数字段: {load_result.get('pregnancy_field', '未识别')}\n"
                            f"💡 现在可以进行隐形乳房炎监测分析，将包含干奶前流行率计算"
                        )
                        
                    else:
                        QMessageBox.warning(self, "加载失败", f"牛群基础信息加载失败: {load_result.get('error', '未知错误')}")
                        
                except ImportError:
                    QMessageBox.critical(self, "模块缺失", "缺少隐形乳房炎监测模块，请检查安装。")
                except Exception as e:
                    QMessageBox.critical(self, "处理失败", f"牛群基础信息处理失败: {str(e)}")
                    
            else:
                QMessageBox.warning(self, "处理失败", f"牛群基础信息处理失败: {message}")
                
        except Exception as e:
            QMessageBox.critical(self, "上传失败", f"牛群基础信息上传失败: {str(e)}")
    
    def check_monitoring_analysis_ready(self):
        """检查隐形乳房炎监测分析是否准备就绪"""
        if hasattr(self, 'mastitis_monitoring_calculator') and self.mastitis_monitoring_calculator:
            # 检查是否有DHI数据
            has_dhi_data = hasattr(self.mastitis_monitoring_calculator, 'monthly_data') and \
                          self.mastitis_monitoring_calculator.monthly_data
            
            # 启用分析按钮
            if has_dhi_data:
                self.analyze_monitoring_btn.setEnabled(True)
                logger.info("隐形乳房炎监测分析已准备就绪")
            else:
                self.analyze_monitoring_btn.setEnabled(False)
        else:
            self.analyze_monitoring_btn.setEnabled(False)
    
    def start_heartbeat(self):
        """启动心跳机制"""
        if self.heartbeat_timer:
            self.heartbeat_timer.stop()
        
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        self.heartbeat_timer.start(90000)  # 90秒
        
        # 立即发送一次心跳
        self.send_heartbeat()
    
    def send_heartbeat(self):
        """发送心跳"""
        if self.auth_service:
            success = self.auth_service.heartbeat()
            if not success:
                # 会话失效，需要重新登录
                self.heartbeat_timer.stop()
                QMessageBox.warning(
                    self,
                    "会话失效",
                    "您的登录会话已失效，请重新登录。"
                )
                self.logout()
    
    def logout(self):
        """注销"""
        reply = QMessageBox.question(
            self,
            "确认注销",
            "确定要退出登录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 停止心跳
            if self.heartbeat_timer:
                self.heartbeat_timer.stop()
            
            # 调用注销接口
            if self.auth_service:
                self.auth_service.logout()
            
            # 关闭主窗口
            self.close()
            
            # 重新显示登录对话框
            login_dialog = LoginDialog(None, self.auth_service)
            if login_dialog.exec() == QDialog.DialogCode.Accepted:
                # 登录成功，创建新的主窗口
                new_window = MainWindow(
                    username=login_dialog.get_username(),
                    auth_service=self.auth_service
                )
                new_window.showMaximized()
            else:
                # 用户取消登录，退出应用
                QApplication.quit()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止心跳
        if self.heartbeat_timer:
            self.heartbeat_timer.stop()
        
        # 注销
        if self.auth_service:
            self.auth_service.logout()
        
        event.accept()


class DHIDesktopApp:
    """DHI桌面应用程序"""
    
    def __init__(self):
        self.app = None
        self.window = None
        self.auth_service = None
        self.username = None
    
    def run(self):
        """运行应用程序"""
        try:
            # 启用高DPI支持
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
            
            # 创建QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("DHI筛查助手")
            self.app.setApplicationVersion("2.0.0")
            self.app.setOrganizationName("DHI")
            self.app.setOrganizationDomain("dhi.com")
            self.app.setStyle('Fusion')  # 使用现代样式
            
            # 设置应用程序图标
            try:
                if os.path.exists("whg3r-qi1nv-001.ico"):
                    self.app.setWindowIcon(QIcon("whg3r-qi1nv-001.ico"))
            except:
                pass
            
            # 创建简化的认证服务（直接连接阿里云数据库）
            print("正在连接认证服务...")
            self.auth_service = SimpleAuthService()
            
            # 检查数据库连接
            if not self.auth_service.check_server_health():
                QMessageBox.critical(
                    None,
                    "数据库连接失败",
                    "无法连接到数据库。\n请检查网络连接后重试。"
                )
                return 0
            
            # 显示登录对话框
            login_dialog = LoginDialog(None, self.auth_service)
            if login_dialog.exec() == QDialog.DialogCode.Accepted:
                self.username = login_dialog.get_username()
            else:
                # 用户取消登录
                return 0
            
            # 创建主窗口，传入用户名和认证服务
            self.window = MainWindow(username=self.username, auth_service=self.auth_service)
            self.window.showMaximized()  # 自动最大化显示
            
            # 运行事件循环
            return self.app.exec()
            
        except Exception as e:
            print(f"应用程序启动失败: {e}")
            if self.app:
                QMessageBox.critical(
                    None,
                    "启动失败", 
                    f"应用程序启动失败:\n{e}"
                )
            return 1


def main():
    """主函数"""
    try:
        app = DHIDesktopApp()
        return app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())