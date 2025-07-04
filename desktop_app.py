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
    QColorDialog, QInputDialog, QLineEdit
)
from PyQt6.QtCore import QThread, pyqtSignal, QDate, Qt, QTimer, QSettings
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QAction
import yaml

# 导入我们的数据处理模块
from data_processor import DataProcessor
from models import FilterConfig


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
        
        self.init_ui(current_scale, current_font_color, current_bg_color, 
                    current_font_family, current_font_size, current_font_bold, 
                    current_font_italic, current_font_underline)
    
    def init_ui(self, current_scale, current_font_color, current_bg_color,
                current_font_family, current_font_size, current_font_bold,
                current_font_italic, current_font_underline):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("界面显示设置")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
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
            self.current_font_color = color.name()
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
        self.settings.sync()
        
        return scale, font_color, bg_color, font_family, font_size, font_bold, font_italic, font_underline


class FarmIdUnificationDialog(QDialog):
    """牧场编号统一选择对话框"""
    
    def __init__(self, farm_id_files_map: Dict[str, List[str]], parent=None):
        super().__init__(parent)
        self.farm_id_files_map = farm_id_files_map
        self.selected_farm_id = None
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("牧场编号统一")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题和说明
        title_label = QLabel("发现多个不同的牧场编号")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel("系统检测到上传的文件包含不同的牧场编号。\n为确保数据一致性，请选择一个牧场编号统一所有数据：")
        desc_label.setStyleSheet("font-size: 14px; color: #333; margin-bottom: 15px; line-height: 1.4;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 牧场编号选择区域
        selection_frame = QFrame()
        selection_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        selection_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 15px;
            }
        """)
        selection_layout = QVBoxLayout(selection_frame)
        
        # 单选按钮组
        from PyQt6.QtWidgets import QButtonGroup, QRadioButton
        self.button_group = QButtonGroup()
        self.radio_buttons = {}
        
        for i, (farm_id, files) in enumerate(self.farm_id_files_map.items()):
            # 创建单选按钮
            radio_btn = QRadioButton()
            radio_btn.setStyleSheet("""
                QRadioButton {
                    font-size: 14px;
                    color: #333;
                    spacing: 10px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
                QRadioButton::indicator:unchecked {
                    border: 2px solid #bdc3c7;
                    border-radius: 9px;
                    background-color: white;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #3498db;
                    border-radius: 9px;
                    background-color: #3498db;
                }
            """)
            
            # 设置文本
            files_count = len(files)
            files_preview = "、".join(files[:3])
            if files_count > 3:
                files_preview += f"等{files_count}个文件"
            else:
                files_preview += f"共{files_count}个文件"
            
            radio_text = f"牧场编号：{farm_id}  ({files_preview})"
            radio_btn.setText(radio_text)
            
            # 默认选择第一个
            if i == 0:
                radio_btn.setChecked(True)
                self.selected_farm_id = farm_id
            
            # 连接信号
            radio_btn.toggled.connect(lambda checked, fid=farm_id: self.on_farm_id_selected(checked, fid))
            
            self.button_group.addButton(radio_btn, i)
            self.radio_buttons[farm_id] = radio_btn
            selection_layout.addWidget(radio_btn)
            
            # 添加文件详情（可折叠）
            if files_count > 3:
                details_label = QLabel(f"   完整文件列表：{', '.join(files)}")
                details_label.setStyleSheet("font-size: 12px; color: #666; margin-left: 30px; margin-bottom: 10px;")
                details_label.setWordWrap(True)
                selection_layout.addWidget(details_label)
        
        layout.addWidget(selection_frame)
        
        # 警告信息
        warning_frame = QFrame()
        warning_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 6px;
                padding: 12px;
                margin: 10px 0;
            }
        """)
        warning_layout = QHBoxLayout(warning_frame)
        
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 18px;")
        warning_layout.addWidget(warning_icon)
        
        warning_text = QLabel("注意：选择统一牧场编号后，所有文件中的牧场编号都将被更新为所选编号。此操作不可撤销。")
        warning_text.setStyleSheet("font-size: 13px; color: #856404; font-weight: bold;")
        warning_text.setWordWrap(True)
        warning_layout.addWidget(warning_text)
        
        layout.addWidget(warning_frame)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 取消按钮
        cancel_btn = QPushButton("❌ 取消上传")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        # 确定按钮
        confirm_btn = QPushButton("✅ 确认统一")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(confirm_btn)
        
        layout.addLayout(button_layout)
    
    def on_farm_id_selected(self, checked: bool, farm_id: str):
        """当选择牧场编号时"""
        if checked:
            self.selected_farm_id = farm_id
    
    def get_selected_farm_id(self) -> str:
        """获取选择的牧场编号"""
        return self.selected_farm_id or ""


class BatchFarmIdInputDialog(QDialog):
    """批量管理号输入对话框"""
    
    def __init__(self, missing_files, parent=None):
        super().__init__(parent)
        self.missing_files = missing_files  # 缺少管理号的文件列表
        self.farm_id_inputs = {}  # 存储输入框
        self.setWindowTitle("批量输入牛场编号")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题说明
        title_label = QLabel("以下文件缺少牛场编号，请为每个文件输入对应的牛场编号：")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #d32f2f; padding: 10px; background-color: #ffebee; border-radius: 5px;")
        layout.addWidget(title_label)
        
        # 创建滚动区域以支持大量文件
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 为每个缺少管理号的文件创建输入行
        for file_info in self.missing_files:
            filename = file_info.get('filename', 'Unknown')
            source_info = file_info.get('source_info', '')
            
            # 创建文件信息组
            file_group = QGroupBox(f"文件: {filename}")
            file_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
            
            file_layout = QVBoxLayout(file_group)
            
            # 显示来源信息
            if source_info:
                source_label = QLabel(f"来源: {source_info}")
                source_label.setStyleSheet("color: #666666; font-size: 10px; margin-bottom: 5px;")
                file_layout.addWidget(source_label)
            
            # 输入框布局
            input_layout = QHBoxLayout()
            
            # 牛场编号标签
            label = QLabel("牛场编号:")
            label.setMinimumWidth(80)
            label.setStyleSheet("font-weight: bold; color: #333333;")
            input_layout.addWidget(label)
            
            # 输入框
            farm_id_input = QLineEdit()
            farm_id_input.setPlaceholderText("请输入牛场编号（如：123456）")
            farm_id_input.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid #ddd;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #007bff;
                }
                QLineEdit:hover {
                    border-color: #0056b3;
                }
            """)
            input_layout.addWidget(farm_id_input)
            
            # 保存输入框引用
            self.farm_id_inputs[filename] = farm_id_input
            
            file_layout.addLayout(input_layout)
            scroll_layout.addWidget(file_group)
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(400)  # 限制最大高度
        layout.addWidget(scroll_area)
        
        # 操作说明
        hint_label = QLabel("💡 提示：同一批次的所有数据将使用相同的牛场编号")
        hint_label.setStyleSheet("color: #666666; font-style: italic; padding: 5px;")
        layout.addWidget(hint_label)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        # 全部设置为相同值按钮
        set_all_btn = QPushButton("全部设为相同编号")
        set_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
        """)
        set_all_btn.clicked.connect(self.set_all_same)
        button_layout.addWidget(set_all_btn)
        
        button_layout.addStretch()
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 设置对话框大小
        self.resize(600, min(150 + len(self.missing_files) * 120, 600))
    
    def set_all_same(self):
        """设置所有文件为相同的牛场编号"""
        farm_id, ok = QInputDialog.getText(
            self, 
            "设置牛场编号", 
            "请输入要应用到所有文件的牛场编号:",
            text=""
        )
        
        if ok and farm_id.strip():
            farm_id = farm_id.strip()
            # 将相同的值应用到所有输入框
            for input_widget in self.farm_id_inputs.values():
                input_widget.setText(farm_id)
    
    def accept(self):
        """确认输入"""
        # 验证所有输入
        missing_inputs = []
        for filename, input_widget in self.farm_id_inputs.items():
            farm_id = input_widget.text().strip()
            if not farm_id:
                missing_inputs.append(filename)
        
        if missing_inputs:
            QMessageBox.warning(
                self, 
                "输入不完整", 
                f"以下文件的牛场编号不能为空:\n" + "\n".join(missing_inputs)
            )
            return
        
        # 验证牛场编号格式（可选）
        invalid_inputs = []
        for filename, input_widget in self.farm_id_inputs.items():
            farm_id = input_widget.text().strip()
            if not farm_id.isdigit() or len(farm_id) < 3:
                invalid_inputs.append(f"{filename}: {farm_id}")
        
        if invalid_inputs:
            reply = QMessageBox.question(
                self,
                "格式验证",
                f"以下牛场编号格式可能不正确（建议使用3位以上纯数字）:\n" + 
                "\n".join(invalid_inputs) + 
                "\n\n是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        super().accept()
    
    def get_farm_ids(self):
        """获取所有输入的牛场编号"""
        result = {}
        for filename, input_widget in self.farm_id_inputs.items():
            result[filename] = input_widget.text().strip()
        return result


class FileProcessThread(QThread):
    """文件处理线程"""
    progress_updated = pyqtSignal(str, int)  # 状态信息, 进度百分比
    file_processed = pyqtSignal(str, bool, str, dict)  # 文件名, 成功, 消息, 数据信息
    processing_completed = pyqtSignal(dict)  # 完成信息
    log_updated = pyqtSignal(str)  # 处理过程日志
    
    def __init__(self, file_paths, filenames):
        super().__init__()
        self.file_paths = file_paths
        self.filenames = filenames
        self.processor = DataProcessor()
        
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
                current_progress = 10 + int((i / total_files) * 70)  # 10-80% for file processing
                
                self.log_updated.emit(f"\n📄 正在处理文件 {i+1}/{total_files}: {filename}")
                self.progress_updated.emit(f"处理文件 {i+1}/{total_files}: {filename}", current_progress)
                
                try:
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
    
    def __init__(self, data_list, filters, selected_files, processor=None):
        super().__init__()
        self.data_list = data_list
        self.filters = filters
        self.selected_files = selected_files
        self.processor = processor if processor else DataProcessor()
        self._should_stop = False  # 停止标志
    
    def stop(self):
        """停止筛选"""
        self._should_stop = True
        self.log_updated.emit("⏹️ 用户请求停止筛选...")
    
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
                if filter_config.get('enabled', False) and filter_name not in ['farm_id', 'parity', 'date_range']:
                    enabled_filters.append(filter_name)
            
            self.log_updated.emit(f"📋 启用的筛选项: {enabled_filters if enabled_filters else '仅基础筛选'}")
            
            self.progress_updated.emit("统计数据规模...", 10)
            
            # 计算全部数据的牛头数
            all_cows = set()
            for item in self.data_list:
                df = item['data']
                if 'farm_id' in df.columns and 'management_id' in df.columns:
                    cow_pairs = df[['farm_id', 'management_id']].dropna()
                    for _, row in cow_pairs.iterrows():
                        all_cows.add((row['farm_id'], row['management_id']))
            
            self.log_updated.emit(f"📊 全部数据: {len(all_cows)} 头牛")
            
            # 计算筛选范围的牛头数
            range_cows = set()
            selected_data = [item for item in self.data_list if item['filename'] in self.selected_files]
            for item in selected_data:
                df = item['data']
                if 'farm_id' in df.columns and 'management_id' in df.columns:
                    cow_pairs = df[['farm_id', 'management_id']].dropna()
                    for _, row in cow_pairs.iterrows():
                        range_cows.add((row['farm_id'], row['management_id']))
            
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
            display_fields = ['farm_id', 'management_id', 'parity']
            
            # 添加启用的筛选项到display_fields
            # 定义所有支持的字段
            supported_fields = [
                'protein_pct', 'somatic_cell_count', 'fat_pct', 'lactose_pct', 
                'milk_yield', 'lactation_days', 'solids_pct', 'fat_protein_ratio',
                'urea_nitrogen', 'total_fat_pct', 'total_protein_pct', 'mature_equivalent',
                'somatic_cell_score', 'freezing_point', 'total_bacterial_count',
                'dry_matter_intake', 'net_energy_lactation', 'metabolizable_protein',
                'crude_protein', 'neutral_detergent_fiber', 'acid_detergent_fiber',
                'starch', 'ether_extract', 'ash', 'calcium', 'phosphorus', 
                'magnesium', 'sodium', 'potassium', 'sulfur'
            ]
            
            for filter_name in enabled_filters:
                if filter_name in supported_fields:
                    display_fields.append(filter_name)
            
            # 确保包含必要的字段
            if 'lactation_days' not in display_fields:
                display_fields.append('lactation_days')
            
            # 如果启用了蛋白率筛选，确保包含产奶量用于加权平均计算
            if 'protein_pct' in display_fields and 'milk_yield' not in display_fields:
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
            if not monthly_report.empty and 'farm_id' in monthly_report.columns and 'management_id' in monthly_report.columns:
                cow_pairs = monthly_report[['farm_id', 'management_id']].dropna()
                for _, row in cow_pairs.iterrows():
                    result_cows.add((row['farm_id'], row['management_id']))
            
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
    
    def __init__(self):
        super().__init__()
        self.data_list = []  # 存储所有处理过的数据
        self.processor = DataProcessor()
        self.current_results = pd.DataFrame()  # 当前筛选结果
        
        # 加载显示设置
        self.settings = QSettings("DHI", "ProteinScreening")
        self.display_scale = self.settings.value("display_scale", 100, type=int)
        self.font_color = self.settings.value("font_color", "#000000", type=str)
        self.background_color = self.settings.value("background_color", "#ffffff", type=str)
        self.font_family = self.settings.value("font_family", "Microsoft YaHei", type=str)
        self.font_size = self.settings.value("font_size", 12, type=int)
        self.font_bold = self.settings.value("font_bold", False, type=bool)
        self.font_italic = self.settings.value("font_italic", False, type=bool)
        self.font_underline = self.settings.value("font_underline", False, type=bool)
        
        self.init_ui()
        self.load_config()
    
    def get_safe_screen_info(self):
        """安全地获取屏幕信息"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return {
                'width': 1920,
                'height': 1080,
                'dpi_ratio': 1.0
            }
        else:
            geometry = screen.availableGeometry()
            return {
                'width': geometry.width(),
                'height': geometry.height(),
                'dpi_ratio': screen.devicePixelRatio()
            }
    
    def safe_show_status_message(self, message: str):
        """安全地显示状态栏消息"""
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(message)
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("DHI智能筛选大师")
        
        # 创建菜单栏
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
        
        # 设置全局样式 - 支持DPI缩放和用户设置的字体样式
        dpi_ratio = screen_info['dpi_ratio']
        # 应用用户设置的缩放比例和字体大小
        scale_factor = self.display_scale / 100.0
        user_font_size = self.font_size * scale_factor
        base_font_size = max(int(user_font_size * dpi_ratio * 0.6), 8)
        
        # 构建字体样式字符串
        font_weight = "bold" if self.font_bold else "normal"
        font_style = "italic" if self.font_italic else "normal"
        text_decoration = "underline" if self.font_underline else "none"
        
        # 应用用户设置的颜色和字体样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #f8f9fa;
                color: {self.font_color};
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif;
                font-size: {base_font_size}px;
                font-weight: {font_weight};
                font-style: {font_style};
            }}
            QWidget {{
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif;
                font-size: {base_font_size}px;
                color: {self.font_color};
                font-weight: {font_weight};
                font-style: {font_style};
            }}
            
            /* 主要工作面板的框架保持透明或灰色 */
            QScrollArea {{
                background-color: #f8f9fa;
                border: 1px solid #ddd;
            }}
            QScrollArea > QWidget {{
                background-color: #f8f9fa;
            }}
            
            /* 右侧结果面板框架 */
            QTabWidget {{
                background-color: #f8f9fa;
                color: {self.font_color};
            }}
            QTabWidget::pane {{
                background-color: #f8f9fa;
                border: 1px solid #ddd;
            }}
            QTabBar::tab {{
                color: {self.font_color};
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: #ffffff;
                border-bottom: 2px solid #007bff;
            }}
            
            /* 重点：强制应用输入控件背景色和字体样式，移除系统默认样式 */
            QLineEdit {{
                color: {self.font_color} !important;
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
                padding: 6px !important;
                border-radius: 4px !important;
                selection-background-color: #007bff !important;
                selection-color: white !important;
                outline: none !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QLineEdit:focus {{
                border: 2px solid #007bff !important;
                background-color: {self.background_color} !important;
                outline: none !important;
            }}
            QLineEdit:hover {{
                background-color: {self.background_color} !important;
            }}
            
            QSpinBox, QDoubleSpinBox {{
                color: {self.font_color} !important;
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
                padding: 6px !important;
                border-radius: 4px !important;
                selection-background-color: #007bff !important;
                selection-color: white !important;
                outline: none !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid #007bff !important;
                background-color: {self.background_color} !important;
                outline: none !important;
            }}
            QSpinBox:hover, QDoubleSpinBox:hover {{
                background-color: {self.background_color} !important;
            }}
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
            }}
            
            QComboBox {{
                color: {self.font_color} !important;
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
                padding: 6px !important;
                border-radius: 4px !important;
                min-width: 6em !important;
                outline: none !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QComboBox:focus {{
                border: 2px solid #007bff !important;
                background-color: {self.background_color} !important;
                outline: none !important;
            }}
            QComboBox:hover {{
                background-color: {self.background_color} !important;
            }}
            QComboBox::drop-down {{
                background-color: {self.background_color} !important;
                border: none !important;
                width: 20px !important;
            }}
            QComboBox::down-arrow {{
                border: none !important;
                width: 12px !important;
                height: 12px !important;
            }}
            QComboBox QAbstractItemView {{
                color: {self.font_color} !important;
                background-color: {self.background_color} !important;
                selection-background-color: #e9ecef !important;
                border: 1px solid #ccc !important;
            }}
            
            QDateEdit {{
                color: {self.font_color} !important;
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
                padding: 6px !important;
                border-radius: 4px !important;
                outline: none !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QDateEdit:focus {{
                border: 2px solid #007bff !important;
                background-color: {self.background_color} !important;
                outline: none !important;
            }}
            QDateEdit:hover {{
                background-color: {self.background_color} !important;
            }}
            QDateEdit::drop-down {{
                background-color: {self.background_color} !important;
                border: none !important;
                width: 20px !important;
            }}
            QDateEdit::up-button, QDateEdit::down-button {{
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
            }}
            
            /* 表格显示区域 */
            QTableWidget {{
                color: {self.font_color} !important;
                background-color: {self.background_color} !important;
                gridline-color: #ddd !important;
                alternate-background-color: {self.background_color} !important;
                selection-background-color: #e3f2fd !important;
                selection-color: {self.font_color} !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QTableWidget::item {{
                color: {self.font_color} !important;
                background-color: {self.background_color} !important;
                border: none !important;
                padding: 4px !important;
            }}
            QTableWidget::item:selected {{
                background-color: #e3f2fd !important;
                color: {self.font_color} !important;
            }}
            QHeaderView::section {{
                color: {self.font_color} !important;
                background-color: #f0f0f0 !important;
                border: 1px solid #ccc !important;
                padding: 6px !important;
                font-weight: bold !important;
            }}
            
            /* 文本显示区域 */
            QTextEdit {{
                color: {self.font_color} !important;
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
                border-radius: 4px !important;
                padding: 8px !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QTextEdit:focus {{
                border: 2px solid #007bff !important;
                background-color: {self.background_color} !important;
            }}
            
            /* 其他控件保持透明背景 */
            QLabel {{
                color: {self.font_color} !important;
                background-color: transparent !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
                text-decoration: {text_decoration} !important;
            }}
            QPushButton {{
                color: {self.font_color} !important;
                background-color: #e9ecef !important;
                border: 1px solid #ccc !important;
                padding: 8px 16px !important;
                border-radius: 4px !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QPushButton:hover {{
                background-color: #dee2e6 !important;
            }}
            QPushButton:pressed {{
                background-color: #d3d9df !important;
            }}
            QPushButton:disabled {{
                background-color: #f8f9fa !important;
                color: #6c757d !important;
            }}
            
            QCheckBox {{
                color: {self.font_color} !important;
                background-color: transparent !important;
                spacing: 6px !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QCheckBox::indicator {{
                width: 16px !important;
                height: 16px !important;
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
                border-radius: 3px !important;
            }}
            QCheckBox::indicator:checked {{
                background-color: #007bff !important;
                border: 1px solid #007bff !important;
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid #007bff !important;
                background-color: {self.background_color} !important;
            }}
            
            QRadioButton {{
                color: {self.font_color} !important;
                background-color: transparent !important;
                spacing: 6px !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QRadioButton::indicator {{
                width: 16px !important;
                height: 16px !important;
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
                border-radius: 8px !important;
            }}
            QRadioButton::indicator:checked {{
                background-color: #007bff !important;
                border: 1px solid #007bff !important;
            }}
            QRadioButton::indicator:hover {{
                border: 1px solid #007bff !important;
                background-color: {self.background_color} !important;
            }}
            
            QGroupBox {{
                color: {self.font_color} !important;
                border: 1px solid #ccc !important;
                border-radius: 6px !important;
                margin-top: 10px !important;
                background-color: transparent !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QGroupBox::title {{
                color: {self.font_color} !important;
                subcontrol-origin: margin !important;
                left: 12px !important;
                padding: 0 8px 0 8px !important;
                background-color: #f8f9fa !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            
            /* 进度条样式 */
            QProgressBar {{
                background-color: {self.background_color} !important;
                border: 1px solid #ccc !important;
                border-radius: 4px !important;
                color: {self.font_color} !important;
                text-align: center !important;
                font-family: '{self.font_family}', 'Microsoft YaHei', 'SimHei', sans-serif !important;
                font-weight: {font_weight} !important;
                font-style: {font_style} !important;
            }}
            QProgressBar::chunk {{
                background-color: #007bff !important;
                border-radius: 3px !important;
            }}
            
            /* 移除任何可能导致意外颜色的默认样式 */
            * {{
                outline: none !important;
            }}
        """)
        
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
        
        # 左侧控制面板 - 添加滚动区域
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setMinimumWidth(420)
        left_scroll.setMaximumWidth(600)
        
        left_panel = self.create_control_panel()
        left_scroll.setWidget(left_panel)
        content_splitter.addWidget(left_scroll)
        
        # 右侧结果显示
        right_panel = self.create_result_panel()
        right_panel.setMinimumWidth(500)
        content_splitter.addWidget(right_panel)
        
        # 设置分割器比例和约束
        content_splitter.setSizes([int(window_width * 0.4), int(window_width * 0.6)])
        content_splitter.setCollapsible(0, False)
        content_splitter.setCollapsible(1, False)
        
        # 设置分割器样式
        content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                width: 3px;
                margin: 2px;
            }
            QSplitter::handle:hover {
                background-color: #007bff;
            }
        """)
        
        main_layout.addWidget(content_splitter)
        
        # 状态栏
        self.setup_status_bar()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        if menubar is None:
            return
        
        # 设置菜单栏样式
        scale_factor = self.display_scale / 100.0
        menu_font_size = max(int(12 * scale_factor), 10)
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                font-size: {menu_font_size}px;
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
                font-size: {menu_font_size}px;
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
        
        settings_menu.addSeparator()
        
        # 关于
        about_action = QAction("关于", self)
        about_action.setStatusTip("关于DHI智能筛选大师")
        about_action.triggered.connect(self.show_about)
        settings_menu.addAction(about_action)
    
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
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于DHI智能筛选大师",
                          "DHI智能筛选大师 v2.6\n\n"
                         "用于处理DHI报告中的蛋白质筛选数据\n"
                         "支持批量文件处理和多种筛选条件\n\n"
                         "如有问题请联系技术支持")
    
    def restart_application(self):
        """重启应用程序"""
        import subprocess
        import sys
        
        QApplication.quit()
        subprocess.Popen([sys.executable] + sys.argv)
    
    def setup_status_bar(self):
        """设置状态栏"""
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage("准备就绪")
            screen_info = self.get_safe_screen_info()
            dpi_ratio = screen_info['dpi_ratio']
            status_font_size = max(int(14 * dpi_ratio * 0.8), 12)
            status_bar.setStyleSheet(f"""
                QStatusBar {{
                    background-color: #e9ecef;
                    border-top: 1px solid #dee2e6;
                    padding: 8px 15px;
                    font-size: {status_font_size}px;
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
        margin = max(int(header_height * 0.25), 15)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # 左侧图标和标题
        title_layout = QHBoxLayout()
        
        # 图标
        icon_label = QLabel("🥛")
        icon_size = max(int(header_height * 0.15), 12)
        icon_label.setStyleSheet(f"font-size: {icon_size}px; background: transparent;")
        title_layout.addWidget(icon_label)
        
        # 标题文字
        title_label = QLabel("奶牛蛋白筛查系统")
        title_font_size = max(int(header_height * 0.12), 12)
        title_label.setStyleSheet(f"""
            font-size: {title_font_size}px;
            font-weight: bold;
            color: white;
            background: transparent;
            margin-left: 10px;
        """)
        title_layout.addWidget(title_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
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
                font-size: {max(int(header_height * 0.08), 10)}px;
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
        subtitle_label = QLabel("DHI报告 04-2综合测定结果表筛查工具")
        subtitle_font_size = max(int(header_height * 0.07), 9)
        subtitle_label.setStyleSheet(f"""
            font-size: {subtitle_font_size}px;
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
        """创建卡片样式的容器"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        
        # 添加标题
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 8px 8px 0 0;
                padding: 10px 15px;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            background: transparent;
        """)
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
        """获取自适应按钮样式"""
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        scale_factor = self.display_scale / 100.0
        
        # 基础尺寸
        font_size = max(int(13 * dpi_ratio * 0.7 * scale_factor), 10)
        padding_v = max(int(6 * dpi_ratio * 0.6 * scale_factor), 4)
        padding_h = max(int(12 * dpi_ratio * 0.6 * scale_factor), 6)
        border_radius = max(int(5 * dpi_ratio * 0.6 * scale_factor), 3)
        
        return {
            'primary': f"""
                QPushButton {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: {border_radius}px;
                    padding: {padding_v}px {padding_h}px;
                    font-size: {font_size}px;
                    font-weight: bold;
                    min-height: {padding_v * 2 + font_size}px;
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
                    font-size: {font_size}px;
                    font-weight: bold;
                    min-height: {padding_v * 2 + font_size}px;
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
                    font-size: {font_size}px;
                    font-weight: bold;
                    min-height: {padding_v * 2 + font_size}px;
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
                    font-size: {font_size}px;
                    font-weight: bold;
                    min-height: {padding_v * 2 + font_size}px;
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
            """
        }
    
    def get_responsive_form_styles(self):
        """获取自适应表单样式"""
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        scale_factor = self.display_scale / 100.0
        
        font_size = max(int(13 * dpi_ratio * 0.7 * scale_factor), 10)
        padding_v = max(int(4 * dpi_ratio * 0.6 * scale_factor), 2)
        padding_h = max(int(8 * dpi_ratio * 0.6 * scale_factor), 4)
        border_radius = max(int(4 * dpi_ratio * 0.6 * scale_factor), 2)
        min_height = max(int(20 * dpi_ratio * 0.6 * scale_factor), 16)
        
        return f"""
            QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                border: 1px solid #ced4da;
                border-radius: {border_radius}px;
                padding: {padding_v}px {padding_h}px;
                font-size: {font_size}px;
                background-color: white;
                min-height: {min_height}px;
            }}
            QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
                border-color: #007bff;
                outline: none;
            }}
            QLabel {{
                font-weight: 500;
                color: #495057;
                font-size: {font_size}px;
            }}
        """
    
    def create_control_panel(self):
        """创建左侧控制面板"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(panel)
        
        # 自适应边距和间距
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        scale_factor = self.display_scale / 100.0
        margin = max(int(15 * dpi_ratio * scale_factor), 8)
        spacing = max(int(15 * dpi_ratio * scale_factor), 8)
        
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # 获取自适应样式
        button_styles = self.get_responsive_button_styles()
        form_styles = self.get_responsive_form_styles()
        
        # 获取扩展按钮样式
        button_styles.update({
            'secondary': f"""
                QPushButton {{
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: {max(int(8 * dpi_ratio), 6)}px {max(int(16 * dpi_ratio), 12)}px;
                    border-radius: {max(int(4 * dpi_ratio), 3)}px;
                    font-weight: bold;
                    font-size: {max(int(12 * dpi_ratio), 10)}px;
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
                    padding: {max(int(8 * dpi_ratio), 6)}px {max(int(16 * dpi_ratio), 12)}px;
                    border-radius: {max(int(4 * dpi_ratio), 3)}px;
                    font-weight: bold;
                    font-size: {max(int(12 * dpi_ratio), 10)}px;
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
        })
        
        # 1. 文件上传区域
        upload_group = self.create_card_widget("📁 文件上传")
        upload_layout = QVBoxLayout(getattr(upload_group, 'content_widget'))
        card_margin = max(int(12 * dpi_ratio * scale_factor), 6)
        upload_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 文件选择按钮
        self.upload_btn = QPushButton("📤 选择文件")
        self.upload_btn.setStyleSheet(button_styles['primary'])
        self.upload_btn.clicked.connect(self.select_files)
        upload_layout.addWidget(self.upload_btn)
        
        # 文件列表
        self.file_list = QListWidget()
        # 自适应文件列表高度
        list_height = max(int(100 * dpi_ratio), 80)
        self.file_list.setMaximumHeight(list_height)
        
        list_border_radius = max(int(4 * dpi_ratio), 3)
        list_padding = max(int(5 * dpi_ratio), 3)
        item_padding = max(int(5 * dpi_ratio), 3)
        
        self.file_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid #e0e0e0;
                border-radius: {list_border_radius}px;
                background-color: #f8f9fa;
                padding: {list_padding}px;
            }}
            QListWidget::item {{
                padding: {item_padding}px;
                border-bottom: 1px solid #e0e0e0;
            }}
            QListWidget::item:selected {{
                background-color: #007bff;
                color: white;
            }}
        """)
        upload_layout.addWidget(self.file_list)
        
        # 处理按钮
        self.process_btn = QPushButton("⚙️ 处理文件")
        self.process_btn.setStyleSheet(button_styles['success'])
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        upload_layout.addWidget(self.process_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        progress_border_radius = max(int(4 * dpi_ratio), 3)
        progress_padding = max(int(2 * dpi_ratio), 1)
        progress_chunk_radius = max(int(3 * dpi_ratio), 2)
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #e0e0e0;
                border-radius: {progress_border_radius}px;
                text-align: center;
                padding: {progress_padding}px;
                background-color: #f8f9fa;
                min-height: {max(int(20 * dpi_ratio), 16)}px;
            }}
            QProgressBar::chunk {{
                background-color: #007bff;
                border-radius: {progress_chunk_radius}px;
            }}
        """)
        upload_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        label_font_size = max(int(8 * dpi_ratio * 0.5), 8)
        self.progress_label.setStyleSheet(f"color: #6c757d; font-size: {label_font_size}px;")
        upload_layout.addWidget(self.progress_label)
        
        layout.addWidget(upload_group)
        
        # 2. 在群牛文件上传区域
        active_cattle_group = self.create_card_widget("🐄 在群牛文件")
        active_cattle_layout = QVBoxLayout(getattr(active_cattle_group, 'content_widget'))
        active_cattle_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 在群牛文件选择按钮
        self.active_cattle_btn = QPushButton("📋 选择在群牛文件")
        self.active_cattle_btn.setStyleSheet(button_styles['secondary'])
        self.active_cattle_btn.clicked.connect(self.select_active_cattle_file)
        active_cattle_layout.addWidget(self.active_cattle_btn)
        
        # 在群牛文件状态标签
        self.active_cattle_label = QLabel("未上传在群牛文件")
        self.active_cattle_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        active_cattle_layout.addWidget(self.active_cattle_label)
        
        # 清除在群牛按钮
        self.clear_active_cattle_btn = QPushButton("🗑️ 清除在群牛")
        self.clear_active_cattle_btn.setStyleSheet(button_styles['danger'])
        self.clear_active_cattle_btn.clicked.connect(self.clear_active_cattle)
        self.clear_active_cattle_btn.setVisible(False)
        active_cattle_layout.addWidget(self.clear_active_cattle_btn)
        
        layout.addWidget(active_cattle_group)
        
        # 3. 基础筛选条件区域
        basic_filter_group = self.create_card_widget("🔍 基础筛选条件")
        basic_filter_layout = QFormLayout(getattr(basic_filter_group, 'content_widget'))
        basic_filter_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        form_spacing = max(int(12 * dpi_ratio), 8)
        basic_filter_layout.setSpacing(form_spacing)
        
        # 牛场编号选择
        self.farm_combo = QComboBox()
        self.farm_combo.setEditable(True)
        self.farm_combo.setStyleSheet(form_styles)
        basic_filter_layout.addRow("🏭 牛场编号:", self.farm_combo)
        
        # 胎次范围
        parity_layout = QHBoxLayout()
        self.parity_min = QSpinBox()
        self.parity_min.setRange(1, 99)
        self.parity_min.setValue(1)
        self.parity_min.setStyleSheet(form_styles)
        self.parity_max = QSpinBox()
        self.parity_max.setRange(1, 99)
        self.parity_max.setValue(8)
        self.parity_max.setStyleSheet(form_styles)
        parity_layout.addWidget(self.parity_min)
        dash_label = QLabel("—")
        dash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_font_size = max(int(14 * dpi_ratio), 12)
        dash_margin = max(int(8 * dpi_ratio), 6)
        dash_label.setStyleSheet(f"color: #6c757d; margin: 0 {dash_margin}px; font-size: {dash_font_size}px;")
        parity_layout.addWidget(dash_label)
        parity_layout.addWidget(self.parity_max)
        basic_filter_layout.addRow("🐄 胎次范围:", parity_layout)
        
        # 日期范围
        date_layout = QHBoxLayout()
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate(2024, 1, 1))
        self.date_start.setCalendarPopup(True)
        
        # 专门为日期控件设计的样式，避免全黑问题
        date_input_font_size = max(int(14 * dpi_ratio * 0.8), 12)
        date_input_padding = max(int(8 * dpi_ratio * 0.6), 6)
        date_border_radius = max(int(4 * dpi_ratio * 0.6), 3)
        date_styles = f"""
            QDateEdit {{
                border: 2px solid #ced4da;
                border-radius: {date_border_radius}px;
                padding: {date_input_padding}px;
                background-color: white;
                font-size: {date_input_font_size}px;
                color: #495057;
                selection-background-color: #007bff;
                selection-color: white;
            }}
            QDateEdit:focus {{
                border-color: #80bdff;
                outline: none;
            }}
            QDateEdit:hover {{
                border-color: #adb5bd;
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #ced4da;
                background-color: #f8f9fa;
                border-top-right-radius: {date_border_radius}px;
                border-bottom-right-radius: {date_border_radius}px;
            }}
            QDateEdit::drop-down:hover {{
                background-color: #e9ecef;
            }}
            QDateEdit::down-arrow {{
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iIzZjNzU3ZCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
                width: 12px;
                height: 8px;
            }}
        """
        self.date_start.setStyleSheet(date_styles)
        
        self.date_end = QDateEdit()
        self.date_end.setDate(QDate(2025, 12, 31))
        self.date_end.setCalendarPopup(True)
        self.date_end.setStyleSheet(date_styles)
        date_layout.addWidget(self.date_start)
        dash_label3 = QLabel("—")
        dash_label3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_label3.setStyleSheet(f"color: #6c757d; margin: 0 {dash_margin}px; font-size: {dash_font_size}px;")
        date_layout.addWidget(dash_label3)
        date_layout.addWidget(self.date_end)
        basic_filter_layout.addRow("📅 采样日期:", date_layout)
        
        # 计划调群日期
        self.plan_date = QDateEdit()
        self.plan_date.setDate(QDate.currentDate().addDays(30))
        self.plan_date.setCalendarPopup(True)
        self.plan_date.setStyleSheet(date_styles)
        basic_filter_layout.addRow("📆 计划调群日:", self.plan_date)
        
        layout.addWidget(basic_filter_group)
        
        # 4. 蛋白率筛选区域
        protein_filter_group = self.create_special_filter_group("🧪 蛋白率筛选", "protein")
        layout.addWidget(protein_filter_group)
        
        # 5. 体细胞数筛选区域
        somatic_filter_group = self.create_special_filter_group("🔬 体细胞数筛选", "somatic")
        layout.addWidget(somatic_filter_group)
        
        # 6. 其他筛选项目区域
        other_filter_group = self.create_card_widget("⚗️ 其他筛选项目")
        other_filter_layout = QVBoxLayout(getattr(other_filter_group, 'content_widget'))
        other_filter_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 创建多选界面
        multi_select_widget = QWidget()
        multi_select_layout = QVBoxLayout(multi_select_widget)
        
        # 标题和一键添加按钮
        header_layout = QHBoxLayout()
        select_label = QLabel("选择要添加的筛选项目（可多选）:")
        select_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 13px;")
        header_layout.addWidget(select_label)
        
        header_layout.addStretch()
        
        # 一键添加常用筛选项按钮
        quick_add_btn = QPushButton("一键添加常用")
        quick_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        quick_add_btn.clicked.connect(self.quick_add_common_filters)
        header_layout.addWidget(quick_add_btn)
        
        multi_select_layout.addLayout(header_layout)
        
        # 创建滚动区域用于显示筛选项复选框
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(120)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
        """)
        
        # 创建筛选项复选框容器
        checkbox_widget = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(10, 5, 10, 5)
        checkbox_layout.setSpacing(5)
        
        # 获取可选筛选项并创建复选框
        self.filter_checkboxes = {}
        optional_filters = self.processor.rules.get("optional_filters", {})
        
        # 获取屏幕DPI信息用于样式
        screen = QApplication.primaryScreen()
        dpi_ratio = screen.devicePixelRatio()
        checkbox_font_size = max(int(12 * dpi_ratio * 0.7), 11)
        checkbox_spacing = max(int(6 * dpi_ratio * 0.6), 5)
        checkbox_size = max(int(14 * dpi_ratio * 0.6), 12)
        checkbox_border_radius = max(int(2 * dpi_ratio * 0.6), 2)
        
        for filter_key, filter_config in optional_filters.items():
            chinese_name = filter_config.get("chinese_name", filter_key)
            
            checkbox = QCheckBox(chinese_name)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    font-size: {checkbox_font_size}px;
                    color: #495057;
                    spacing: {checkbox_spacing}px;
                    padding: 3px;
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
                    background-color: #007bff !important;
                    border-color: #007bff !important;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDMuNUwzLjUgNkw5IDEiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                }}
                QCheckBox::indicator:checked:hover {{
                    background-color: #0056b3 !important;
                    border-color: #0056b3 !important;
                }}
                QCheckBox:hover {{
                    background-color: #f8f9fa;
                    border-radius: 3px;
                }}
            """)
            
            # 连接信号，当复选框状态改变时自动添加/移除筛选项
            checkbox.toggled.connect(lambda checked, key=filter_key: self.on_filter_checkbox_toggled(key, checked))
            
            self.filter_checkboxes[filter_key] = checkbox
            checkbox_layout.addWidget(checkbox)
        
        checkbox_layout.addStretch()
        scroll_area.setWidget(checkbox_widget)
        multi_select_layout.addWidget(scroll_area)
        
        # 添加操作按钮行
        button_layout = QHBoxLayout()
        
        # 全选按钮
        select_all_btn = QPushButton("全选")
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        select_all_btn.clicked.connect(self.select_all_filters)
        button_layout.addWidget(select_all_btn)
        
        # 清空按钮
        clear_all_btn = QPushButton("清空")
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        clear_all_btn.clicked.connect(self.clear_all_filters)
        button_layout.addWidget(clear_all_btn)
        
        button_layout.addStretch()
        
        # 应用选择按钮
        apply_btn = QPushButton("应用选择")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        apply_btn.clicked.connect(self.apply_selected_filters)
        button_layout.addWidget(apply_btn)
        
        multi_select_layout.addLayout(button_layout)
        other_filter_layout.addWidget(multi_select_widget)
        
        # 动态添加的其他筛选项容器
        self.other_filters_container = QWidget()
        self.other_filters_layout = QVBoxLayout(self.other_filters_container)
        other_filter_layout.addWidget(self.other_filters_container)
        
        # 存储已添加的其他筛选项
        self.added_other_filters = {}
        
        layout.addWidget(other_filter_group)
        
        # 7. 未来泌乳天数复选框和范围
        future_days_group = self.create_card_widget("🔮 未来泌乳天数筛选")
        future_days_layout = QVBoxLayout(getattr(future_days_group, 'content_widget'))
        future_days_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        
        # 定义复选框样式变量
        checkbox_font_size = max(int(13 * dpi_ratio * 0.7), 12)
        checkbox_spacing = max(int(8 * dpi_ratio * 0.6), 6)
        checkbox_size = max(int(16 * dpi_ratio * 0.6), 14)
        checkbox_border_radius = max(int(3 * dpi_ratio * 0.6), 2)
        
        # 复选框
        self.future_days_enabled = QCheckBox("启用未来泌乳天数筛选")
        self.future_days_enabled.setChecked(False)
        self.future_days_enabled.setToolTip("勾选后，会根据设置的范围筛选未来泌乳天数")
        self.future_days_enabled.setStyleSheet(f"""
            QCheckBox {{
                font-size: {checkbox_font_size}px;
                color: #495057;
                spacing: {checkbox_spacing}px;
            }}
            QCheckBox::indicator {{
                width: {checkbox_size}px;
                height: {checkbox_size}px;
                border: 2px solid #ced4da;
                border-radius: {checkbox_border_radius}px;
                background-color: white;
            }}
            QCheckBox::indicator:checked {{
                background-color: #007bff;
                border-color: #007bff;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }}
        """)
        future_days_layout.addWidget(self.future_days_enabled)
        
        # 范围设置
        future_range_layout = QHBoxLayout()
        self.future_days_min = QSpinBox()
        self.future_days_min.setRange(1, 9999)
        self.future_days_min.setValue(1)
        self.future_days_min.setStyleSheet(form_styles)
        self.future_days_max = QSpinBox()
        self.future_days_max.setRange(1, 9999)
        self.future_days_max.setValue(305)
        self.future_days_max.setStyleSheet(form_styles)
        future_range_layout.addWidget(self.future_days_min)
        dash_label4 = QLabel("—")
        dash_label4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_label4.setStyleSheet(f"color: #6c757d; margin: 0 {dash_margin}px; font-size: {dash_font_size}px;")
        future_range_layout.addWidget(dash_label4)
        future_range_layout.addWidget(self.future_days_max)
        
        future_range_widget = QWidget()
        future_range_widget.setLayout(future_range_layout)
        future_days_layout.addWidget(future_range_widget)
        
        # 控制范围设置的启用状态
        def toggle_future_days_range():
            enabled = self.future_days_enabled.isChecked()
            self.future_days_min.setEnabled(enabled)
            self.future_days_max.setEnabled(enabled)
            dash_label4.setEnabled(enabled)
        
        self.future_days_enabled.toggled.connect(toggle_future_days_range)
        toggle_future_days_range()
        
        layout.addWidget(future_days_group)
        
        # 8. 操作按钮
        action_group = self.create_card_widget("🚀 操作")
        action_layout = QVBoxLayout(getattr(action_group, 'content_widget'))
        action_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
        action_spacing = max(int(10 * dpi_ratio), 8)
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
        self.filter_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #e0e0e0;
                border-radius: {progress_border_radius}px;
                text-align: center;
                padding: {progress_padding}px;
                background-color: #f8f9fa;
                min-height: {max(int(20 * dpi_ratio), 16)}px;
            }}
            QProgressBar::chunk {{
                background-color: #ffc107;
                border-radius: {progress_chunk_radius}px;
            }}
        """)
        action_layout.addWidget(self.filter_progress)
        
        self.filter_label = QLabel("")
        filter_label_font_size = max(int(8 * dpi_ratio * 0.5), 8)
        self.filter_label.setStyleSheet(f"color: #6c757d; font-size: {filter_label_font_size}px;")
        action_layout.addWidget(self.filter_label)
        
        layout.addWidget(action_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
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
        
        tab_font_size = max(int(13 * dpi_ratio * 0.7), 12)
        tab_padding_v = max(int(10 * dpi_ratio * 0.6), 8)
        tab_padding_h = max(int(14 * dpi_ratio * 0.6), 10)
        tab_border_radius = max(int(5 * dpi_ratio * 0.6), 4)
        tab_min_width = max(int(70 * dpi_ratio * 0.6), 50)
        
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
        info_font_size = max(int(14 * dpi_ratio * 0.8), 12)
        info_padding = max(int(12 * dpi_ratio * 0.6), 10)
        self.file_info_widget.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                background-color: #f8f9fa;
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
                color: #333;
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
        self.tab_widget.addTab(self.result_table, "📊 筛选结果")
        
        # 筛选分析标签页（合并统计信息）
        self.analysis_widget = self.create_analysis_panel()
        self.tab_widget.addTab(self.analysis_widget, "🎯 筛选分析")
        
        return panel
    
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
        
        tab_font_size = max(int(12 * dpi_ratio * 0.7), 11)
        tab_padding_v = max(int(8 * dpi_ratio * 0.6), 6)
        tab_padding_h = max(int(12 * dpi_ratio * 0.6), 8)
        tab_border_radius = max(int(4 * dpi_ratio * 0.6), 3)
        tab_min_width = max(int(60 * dpi_ratio * 0.6), 45)
        
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
        stats_font_size = max(int(11 * dpi_ratio * 0.7), 10)
        stats_padding = max(int(8 * dpi_ratio * 0.6), 6)
        
        # 通用文本框样式
        text_style = f"""
            QTextEdit {{
                border: 1px solid #bee5eb;
                border-radius: 4px;
                background-color: white;
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
        title_label.setStyleSheet(f"color: #6c757d; font-size: {card_title_font_size}px; margin-bottom: 5px;")
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
        desc_label.setStyleSheet(f"color: #6c757d; font-size: {card_desc_font_size}px;")
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
            "支持的文件 (*.zip *.xlsx);;ZIP文件 (*.zip);;Excel文件 (*.xlsx)"
        )
        
        if files:
            self.file_list.clear()
            self.selected_files = files
            
            for file in files:
                filename = os.path.basename(file)
                item = QListWidgetItem(filename)
                self.file_list.addItem(item)
            
            self.process_btn.setEnabled(True)
            self.safe_show_status_message(f"已选择 {len(files)} 个文件")
    
    def process_files(self):
        """处理文件"""
        if not hasattr(self, 'selected_files') or not self.selected_files:
            return
        
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 启动处理线程
        filenames = [os.path.basename(f) for f in self.selected_files]
        self.process_thread = FileProcessThread(self.selected_files, filenames)
        self.process_thread.progress_updated.connect(self.update_progress)
        self.process_thread.file_processed.connect(self.file_processed)
        self.process_thread.processing_completed.connect(self.processing_completed)
        self.process_thread.log_updated.connect(self.update_process_log)
        self.process_thread.start()
        
        # 切换到处理过程标签页
        self.tab_widget.setCurrentWidget(self.process_log_widget)
    
    def update_progress(self, status, progress):
        """更新进度"""
        self.progress_label.setText(status)
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
    
    def handle_missing_farm_id(self, filename, missing_info):
        """处理缺少牛场编号的情况"""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("缺少牛场编号")
        msg.setText(f"文件 '{missing_info['filename']}' 中缺少牛场编号列。")
        msg.setInformativeText("这可能是老版本的DHI报告。请输入该文件对应的牛场编号：")
        
        # 添加输入框
        farm_id, ok = QInputDialog.getText(
            self, 
            "输入牛场编号", 
            f"请为文件 '{missing_info['filename']}' 输入牛场编号:\n\n注意：该文件中所有牛只都将使用此牛场编号", 
            text=""
        )
        
        if ok and farm_id.strip():
            # 将牛场编号添加到对应的数据中
            self.add_farm_id_to_data(filename, farm_id.strip())
            self.statusBar().showMessage(f"已为 {filename} 设置牛场编号: {farm_id.strip()}")
        else:
            # 用户取消输入，显示警告
            QMessageBox.warning(
                self, 
                "警告", 
                f"未设置牛场编号，文件 '{missing_info['filename']}' 可能无法正常使用。"
            )
    
    def add_farm_id_to_data(self, filename, farm_id):
        """为指定文件的数据添加牛场编号"""
        for data_item in self.data_list:
            if data_item['filename'] == filename:
                df = data_item['data']
                if 'farm_id' not in df.columns:
                    # 添加牛场编号列
                    df['farm_id'] = farm_id
                    logger.info(f"为文件 {filename} 添加牛场编号: {farm_id}")
                    
                    # 移除缺少牛场编号的标记
                    if hasattr(df, 'attrs') and 'missing_farm_id_info' in df.attrs:
                        del df.attrs['missing_farm_id_info']
                    
                    # 更新数据项
                    data_item['data'] = df
                break
    
    def processing_completed(self, results):
        """所有文件处理完成"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        
        # 检查是否有缺少管理号的文件
        missing_farm_id_files = results.get('missing_farm_id_files', [])
        
        if missing_farm_id_files:
            # 弹出批量输入对话框
            self.handle_batch_missing_farm_id(missing_farm_id_files, results)
        else:
            # 没有缺少管理号的文件，检查牧场编号一致性
            self.check_and_handle_farm_id_consistency(results)
    
    def handle_batch_missing_farm_id(self, missing_files, results):
        """处理批量缺少管理号的情况"""
        # 创建批量输入对话框
        dialog = BatchFarmIdInputDialog(missing_files, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 用户确认输入，获取所有牛场编号
            farm_ids = dialog.get_farm_ids()
            
            # 应用牛场编号到对应的数据
            for file_info in missing_files:
                filename = file_info['filename']
                farm_id = farm_ids.get(filename)
                if farm_id:
                    # 更新数据中的牛场编号
                    self.add_farm_id_to_data(filename, farm_id)
            
            # 重新收集牛场编号列表
            all_farm_ids = set(results.get('farm_ids', []))
            for farm_id in farm_ids.values():
                all_farm_ids.add(farm_id)
            results['farm_ids'] = sorted(list(all_farm_ids))
            
            # 在管理号输入完成后，检查牧场编号一致性
            self.check_and_handle_farm_id_consistency(results)
            
            # 显示成功信息
            QMessageBox.information(
                self, 
                "输入完成", 
                f"已成功为 {len(missing_files)} 个文件设置牛场编号，可以开始筛选数据。"
            )
        else:
            # 用户取消，显示警告并完成处理（但这些文件可能无法正常筛选）
            QMessageBox.warning(
                self,
                "输入取消",
                f"已取消为 {len(missing_files)} 个文件输入牛场编号。\n"
                "这些文件的数据将无法正常参与筛选，建议重新处理。"
            )
            # 仍然完成处理，但用户需要知道影响
            self.complete_processing(results)
    
    def check_and_handle_farm_id_consistency(self, results):
        """检查并处理牧场编号一致性"""
        try:
            # 获取所有数据
            all_data = results.get('all_data', [])
            if not all_data:
                self.complete_processing(results)
                return
            
            # 检查牧场编号一致性
            is_consistent, all_farm_ids, farm_id_files_map = self.processor.check_farm_id_consistency(all_data)
            
            if not is_consistent and len(all_farm_ids) > 1:
                # 发现多个不同的牧场编号，显示统一对话框
                dialog = FarmIdUnificationDialog(farm_id_files_map, self)
                
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    # 用户选择了要统一的牧场编号
                    target_farm_id = dialog.get_selected_farm_id()
                    
                    # 统一所有数据的牧场编号
                    unified_data = self.processor.unify_farm_ids(all_data, target_farm_id)
                    
                    # 更新results中的数据
                    results['all_data'] = unified_data
                    
                    # 更新牧场编号列表
                    results['farm_ids'] = [target_farm_id]
                    
                    # 显示统一成功信息
                    QMessageBox.information(
                        self,
                        "牧场编号统一完成",
                        f"已成功将所有数据的牧场编号统一为：{target_farm_id}\n\n" +
                        f"涉及{len(farm_id_files_map)}个不同的牧场编号，" +
                        f"共{sum(len(files) for files in farm_id_files_map.values())}个文件。"
                    )
                    
                    # 完成处理
                    self.complete_processing(results)
                else:
                    # 用户取消了统一，提示风险并询问是否继续
                    reply = QMessageBox.warning(
                        self,
                        "取消牧场编号统一",
                        f"检测到{len(all_farm_ids)}个不同的牧场编号：{', '.join(all_farm_ids)}\n\n" +
                        "不统一牧场编号可能会导致筛选结果不准确。\n" +
                        "是否仍要继续处理？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        # 用户选择继续，保持原有的多个牧场编号
                        self.complete_processing(results)
                    else:
                        # 用户选择取消，重置数据
                        self.data_list = []
                        self.file_info_widget.clear()
                        self.file_info_widget.append("❌ 已取消文件处理。请重新上传文件。")
                        self.statusBar().showMessage("已取消文件处理")
            else:
                # 牧场编号一致或只有一个牧场编号，直接完成处理
                self.complete_processing(results)
                
        except Exception as e:
            # 如果检查过程出错，记录错误并继续处理
            import traceback
            error_msg = f"检查牧场编号一致性时出错: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            
            QMessageBox.warning(
                self,
                "牧场编号检查失败",
                f"检查牧场编号一致性时出现错误，将继续处理数据。\n\n错误信息：{str(e)}"
            )
            
            # 仍然完成处理
            self.complete_processing(results)
    
    def complete_processing(self, results):
        """完成处理流程"""
        # 保存数据
        self.data_list = results['all_data']
        
        # 计算总牛头数并更新分析面板
        total_cows = set()
        all_data_combined = []
        
        for item in self.data_list:
            df = item['data']
            all_data_combined.append(df)
            if 'farm_id' in df.columns and 'management_id' in df.columns:
                cow_pairs = df[['farm_id', 'management_id']].dropna()
                for _, row in cow_pairs.iterrows():
                    total_cows.add((row['farm_id'], row['management_id']))
        
        # 合并所有数据用于分析
        if all_data_combined:
            combined_df = pd.concat(all_data_combined, ignore_index=True)
            self.update_filter_ranges(combined_df)
        
        # 更新全部数据统计
        getattr(self.total_data_card, 'value_label').setText(str(len(total_cows)))
        
        # 更新牛场编号选择器
        farm_ids = results['farm_ids']
        self.farm_combo.clear()
        self.farm_combo.addItem("全部牛场")
        self.farm_combo.addItems(farm_ids)
        
        # 检测重复文件并在文件信息框显示
        self.detect_and_display_duplicates()
        
        # 显示处理结果
        success_count = len(results['success_files'])
        failed_count = len(results['failed_files'])
        missing_count = len(results.get('missing_farm_id_files', []))
        
        summary = f"\n📊 处理完成！\n"
        summary += f"成功: {success_count} 个文件\n"
        summary += f"失败: {failed_count} 个文件\n"
        if missing_count > 0:
            summary += f"已补充牛场编号: {missing_count} 个文件\n"
        summary += f"发现牛场: {len(farm_ids)} 个\n\n"
        
        self.file_info_widget.append(summary)
        
        # 启用筛选按钮
        if success_count > 0:
            self.filter_btn.setEnabled(True)
        
        status_msg = f"处理完成：成功 {success_count} 个，失败 {failed_count} 个"
        if missing_count > 0:
            status_msg += f"，已补充牛场编号 {missing_count} 个"
        self.statusBar().showMessage(status_msg)
    
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
                    
                    # 更新日期选择器
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
        if not self.data_list:
            QMessageBox.warning(self, "警告", "请先处理文件")
            return
        
        # 构建筛选条件
        filters = self.build_filters()
        selected_files = [item['filename'] for item in self.data_list]
        
        # 检查是否有启用的特殊筛选项
        special_filters_enabled = False
        special_filter_names = []
        
        for filter_name, filter_config in filters.items():
            if (filter_name not in ['farm_id', 'parity', 'date_range', 'future_lactation_days'] and 
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
        
        # 显示/隐藏按钮
        self.filter_btn.setEnabled(False)
        self.filter_btn.setVisible(False)
        self.cancel_filter_btn.setEnabled(True)
        self.cancel_filter_btn.setVisible(True)
        self.filter_progress.setVisible(True)
        self.filter_progress.setValue(0)
        
        # 启动筛选线程（传递processor实例以共享在群牛数据）
        self.filter_thread = FilterThread(self.data_list, filters, selected_files, self.processor)
        self.filter_thread.progress_updated.connect(self.update_filter_progress)
        self.filter_thread.filtering_completed.connect(self.filtering_completed)
        self.filter_thread.log_updated.connect(self.update_process_log)
        self.filter_thread.start()
        
        # 切换到处理过程标签页
        self.tab_widget.setCurrentWidget(self.process_log_widget)
    
    def build_filters(self):
        """构建筛选条件"""
        filters = {}
        
        # 牛场编号
        farm_id = self.farm_combo.currentText()
        if farm_id and farm_id != "全部牛场":
            filters['farm_id'] = {
                'field': 'farm_id',
                'enabled': True,
                'allowed': [farm_id]
            }
        
        # 胎次
        filters['parity'] = {
            'field': 'parity',
            'enabled': True,
            'min': self.parity_min.value(),
            'max': self.parity_max.value()
        }
        
        # 日期范围
        filters['date_range'] = {
            'field': 'sample_date',
            'enabled': True,
            'start_date': self.date_start.date().toString("yyyy-MM-dd"),
            'end_date': self.date_end.date().toString("yyyy-MM-dd")
        }
        
        # 蛋白率筛选（新的独立筛选项）
        if hasattr(self, 'protein_enabled') and self.protein_enabled.isChecked():
            filters['protein_pct'] = {
                'field': 'protein_pct',
                'enabled': True,
                'min': self.protein_min.value(),
                'max': self.protein_max.value(),
                'min_match_months': self.protein_months.value(),
                'treat_empty_as_match': self.protein_empty.isChecked()
            }
        
        # 体细胞数筛选（新的独立筛选项）
        if hasattr(self, 'somatic_enabled') and self.somatic_enabled.isChecked():
            filters['somatic_cell_count'] = {
                'field': 'somatic_cell_count',
            'enabled': True,
                'min': self.somatic_min.value(),
                'max': self.somatic_max.value(),
                'min_match_months': self.somatic_months.value(),
                'treat_empty_as_match': self.somatic_empty.isChecked()
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
                    'treat_empty_as_match': widget.empty_checkbox.isChecked()
        }
        
        # 未来泌乳天数 - 根据复选框状态决定是否启用
        filters['future_lactation_days'] = {
            'field': 'future_lactation_days',
            'enabled': self.future_days_enabled.isChecked(),
            'min': self.future_days_min.value(),
            'max': self.future_days_max.value(),
            'plan_date': self.plan_date.date().toString("yyyy-MM-dd")
        }
        
        return filters
    
    def update_filter_progress(self, status, progress):
        """更新筛选进度"""
        self.filter_label.setText(status)
        self.filter_progress.setValue(progress)
        self.statusBar().showMessage(status)
    
    def filtering_completed(self, success, message, results_df, stats=None):
        """筛选完成"""
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
        key_fields = ['farm_id', 'management_id', 'parity']
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
            'farm_id': '牛场编号',
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
        
        # 统计唯一牛只数（基于farm_id和management_id）
        if 'farm_id' in df.columns and 'management_id' in df.columns:
            unique_cows = df[['farm_id', 'management_id']].drop_duplicates()
            stats += f"🐄 符合条件牛只数: {len(unique_cows)}头\n"
        
        # 按牛场统计
        if 'farm_id' in df.columns:
            farm_counts = df['farm_id'].value_counts()
            stats += f"\n🏢 各牛场记录数:\n"
            for farm, count in farm_counts.items():
                stats += f"  {farm}: {count} 条\n"
        
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
        
        if not milk_columns and not any(df.columns.str.contains(pattern) for _, pattern, _ in other_trait_patterns):
            stats += "本次筛选结果中暂无其他性状数据。\n"
        
        self.other_traits_stats_widget.setText(stats)
    
    def export_results(self):
        """导出结果"""
        if self.current_results.empty:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
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
                
                # 创建自定义消息框，包含"打开"按钮
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("导出成功")
                msg.setText("结果已保存到:")
                msg.setInformativeText(f"{filename}")
                
                # 添加自定义按钮
                open_btn = msg.addButton("打开文件", QMessageBox.ButtonRole.ActionRole)
                open_folder_btn = msg.addButton("打开文件夹", QMessageBox.ButtonRole.ActionRole)
                ok_btn = msg.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                
                # 设置默认按钮
                msg.setDefaultButton(ok_btn)
                
                # 显示对话框并获取点击的按钮
                result = msg.exec()
                clicked_button = msg.clickedButton()
                
                if clicked_button == open_btn:
                    # 直接打开文件
                    self.open_file(filename)
                elif clicked_button == open_folder_btn:
                    # 打开文件所在文件夹
                    self.open_file_folder(filename)
                
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
            'farm_id': '牛场编号',
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
        
        # 空值处理选项
        empty_checkbox = QCheckBox(f"将{title}数据为空的判断为符合")
        empty_checkbox.setChecked(False)
        empty_checkbox.setToolTip(f"勾选后，如果某月{title}数据为空，将视为符合筛选条件")
        empty_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: {checkbox_font_size}px;
                color: #495057;
                spacing: {checkbox_spacing}px;
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
                background-color: #007bff !important;
                border-color: #007bff !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: #0056b3 !important;
                border-color: #0056b3 !important;
            }}
            QCheckBox::indicator:checked:pressed {{
                background-color: #004085 !important;
                border-color: #004085 !important;
            }}
        """)
        layout.addWidget(empty_checkbox)
        
        # 控制组件启用状态
        def toggle_filter_controls():
            enabled = filter_enabled.isChecked()
            range_widget.setEnabled(enabled)
            months_widget.setEnabled(enabled)
            empty_checkbox.setEnabled(enabled)
        
        filter_enabled.toggled.connect(toggle_filter_controls)
        toggle_filter_controls()  # 初始化状态
        
        # 存储控件引用以便后续访问
        if filter_type == "protein":
            self.protein_enabled = filter_enabled
            self.protein_min = range_min
            self.protein_max = range_max
            self.protein_months = months_spinbox
            self.protein_empty = empty_checkbox
        elif filter_type == "somatic":
            self.somatic_enabled = filter_enabled
            self.somatic_min = range_min
            self.somatic_max = range_max
            self.somatic_months = months_spinbox
            self.somatic_empty = empty_checkbox
        
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
                optional_filters = self.processor.rules.get("optional_filters", {})
                filter_config = optional_filters.get(filter_key, {})
                
                if filter_config:
                    filter_widget = self.create_other_filter_widget(filter_key, filter_config)
                    self.other_filters_layout.addWidget(filter_widget)
                    self.added_other_filters[filter_key] = filter_widget
        else:
            # 移除筛选项
            if filter_key in self.added_other_filters:
                widget = self.added_other_filters[filter_key]
                self.other_filters_layout.removeWidget(widget)
                widget.deleteLater()
                del self.added_other_filters[filter_key]
    
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
    
    def add_other_filter(self, text):
        """添加其他筛选项（保留兼容性）"""
        # 这个方法现在主要用于保持兼容性
        pass
    
    def create_other_filter_widget(self, filter_key: str, filter_config: Dict):
        """创建其他筛选项的界面组件"""
        chinese_name = filter_config.get("chinese_name", filter_key)
        
        # 主容器
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
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
        
        empty_checkbox = QCheckBox("空值判断为符合")
        empty_checkbox.setChecked(filter_config.get("treat_empty_as_match", False))
        
        # 为空值复选框设置同样的改进样式
        empty_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: {checkbox_font_size}px;
                color: #495057;
                spacing: {checkbox_spacing}px;
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
                background-color: #007bff !important;
                border-color: #007bff !important;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: #0056b3 !important;
                border-color: #0056b3 !important;
            }}
            QCheckBox::indicator:checked:pressed {{
                background-color: #004085 !important;
                border-color: #004085 !important;
            }}
        """)
        
        options_layout.addWidget(QLabel("最少符合月数:"))
        options_layout.addWidget(months_spinbox)
        options_layout.addWidget(empty_checkbox)
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
        widget.empty_checkbox = empty_checkbox
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
    
    def cancel_filtering(self):
        """取消筛选"""
        reply = QMessageBox.question(
            self,
            "确认取消",
            "确定要取消当前筛选吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'filter_thread') and self.filter_thread.isRunning():
                self.filter_thread.stop()
                # 等待线程结束，但不要阻塞UI
                QTimer.singleShot(100, self._check_filter_thread_stopped)
    
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
        self.filter_progress.setVisible(False)
        self.filter_btn.setEnabled(True)
        self.filter_btn.setVisible(True)
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
            elif trait == 'fat_pct' and '脂肪率(%)' in col and '年' in col and '月' in col:
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


class DHIDesktopApp:
    """DHI桌面应用程序"""
    
    def __init__(self):
        self.app = None

class DHIDesktopApp:
    """DHI桌面应用程序"""
    
    def __init__(self):
        self.app = None
        self.window = None
    
    def run(self):
        """运行应用程序"""
        try:
            # 启用高DPI支持
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
            
            # 创建QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("DHI智能筛选大师")
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
            
            # 创建主窗口
            self.window = MainWindow()
            self.window.show()
            
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