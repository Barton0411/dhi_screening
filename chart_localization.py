"""
图表本地化模块
为PyQtGraph图表提供中文界面
"""

import pyqtgraph as pg
from PyQt6.QtWidgets import QMenu, QAction
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor


def create_chinese_plot_widget():
    """创建一个中文化的图表部件"""
    plot_widget = ChinesePlotWidget()
    return plot_widget


class ChinesePlotWidget(pg.PlotWidget):
    """中文化的PyQtGraph绘图部件"""
    
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._setup_chinese_menu()
        
    def _setup_chinese_menu(self):
        """设置中文右键菜单"""
        # 禁用默认的右键菜单
        self.setMenuEnabled(False)
        
        # 连接自定义右键菜单
        self.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        
    def _on_mouse_clicked(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.MouseButton.RightButton:
            self._show_chinese_context_menu(event.screenPos())
            
    def _show_chinese_context_menu(self, pos):
        """显示中文右键菜单"""
        menu = QMenu(self)
        
        # 视图菜单
        view_menu = menu.addMenu("视图")
        
        # 自动范围
        auto_range_action = QAction("自动范围", self)
        auto_range_action.triggered.connect(lambda: self.autoRange())
        view_menu.addAction(auto_range_action)
        
        # 重置视图
        reset_view_action = QAction("重置视图", self)
        reset_view_action.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view_action)
        
        view_menu.addSeparator()
        
        # 缩放模式
        zoom_menu = view_menu.addMenu("缩放模式")
        
        # X轴缩放
        x_zoom_action = QAction("仅X轴", self)
        x_zoom_action.setCheckable(True)
        x_zoom_action.triggered.connect(lambda: self._set_zoom_mode('x'))
        zoom_menu.addAction(x_zoom_action)
        
        # Y轴缩放
        y_zoom_action = QAction("仅Y轴", self)
        y_zoom_action.setCheckable(True)
        y_zoom_action.triggered.connect(lambda: self._set_zoom_mode('y'))
        zoom_menu.addAction(y_zoom_action)
        
        # XY轴缩放
        xy_zoom_action = QAction("XY轴", self)
        xy_zoom_action.setCheckable(True)
        xy_zoom_action.setChecked(True)
        xy_zoom_action.triggered.connect(lambda: self._set_zoom_mode('xy'))
        zoom_menu.addAction(xy_zoom_action)
        
        # 导出菜单
        export_menu = menu.addMenu("导出")
        
        # 导出图片
        export_image_action = QAction("导出为图片...", self)
        export_image_action.triggered.connect(self._export_image)
        export_menu.addAction(export_image_action)
        
        # 复制到剪贴板
        copy_action = QAction("复制到剪贴板", self)
        copy_action.triggered.connect(self._copy_to_clipboard)
        export_menu.addAction(copy_action)
        
        # 导出数据
        export_data_action = QAction("导出数据...", self)
        export_data_action.triggered.connect(self._export_data)
        export_menu.addAction(export_data_action)
        
        # 网格菜单
        grid_menu = menu.addMenu("网格")
        
        # 显示/隐藏网格
        toggle_grid_action = QAction("显示/隐藏网格", self)
        toggle_grid_action.triggered.connect(self._toggle_grid)
        grid_menu.addAction(toggle_grid_action)
        
        # 网格透明度
        grid_alpha_menu = grid_menu.addMenu("网格透明度")
        for alpha in [0.1, 0.3, 0.5, 0.7]:
            alpha_action = QAction(f"{int(alpha*100)}%", self)
            alpha_action.triggered.connect(lambda checked, a=alpha: self._set_grid_alpha(a))
            grid_alpha_menu.addAction(alpha_action)
        
        # 坐标轴菜单
        axis_menu = menu.addMenu("坐标轴")
        
        # 显示/隐藏坐标轴
        toggle_axis_action = QAction("显示/隐藏坐标轴", self)
        toggle_axis_action.triggered.connect(self._toggle_axes)
        axis_menu.addAction(toggle_axis_action)
        
        # 对数刻度
        axis_menu.addSeparator()
        log_x_action = QAction("X轴对数刻度", self)
        log_x_action.setCheckable(True)
        log_x_action.triggered.connect(lambda checked: self._set_log_mode('x', checked))
        axis_menu.addAction(log_x_action)
        
        log_y_action = QAction("Y轴对数刻度", self)
        log_y_action.setCheckable(True)
        log_y_action.triggered.connect(lambda checked: self._set_log_mode('y', checked))
        axis_menu.addAction(log_y_action)
        
        # 显示菜单
        menu.exec(QCursor.pos())
        
    def _reset_view(self):
        """重置视图"""
        self.autoRange()
        self.enableAutoRange()
        
    def _set_zoom_mode(self, mode):
        """设置缩放模式"""
        if mode == 'x':
            self.setMouseEnabled(x=True, y=False)
        elif mode == 'y':
            self.setMouseEnabled(x=False, y=True)
        else:  # xy
            self.setMouseEnabled(x=True, y=True)
            
    def _export_image(self):
        """导出图片"""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "导出图表", 
            "chart.png",
            "PNG图片 (*.png);;JPEG图片 (*.jpg);;SVG矢量图 (*.svg)"
        )
        if filename:
            self.grab().save(filename)
            
    def _copy_to_clipboard(self):
        """复制到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setPixmap(self.grab())
        
    def _export_data(self):
        """导出数据"""
        # 这里需要根据实际数据来实现
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "导出数据", "数据导出功能需要根据具体图表类型实现")
        
    def _toggle_grid(self):
        """切换网格显示"""
        x_visible = self.getAxis('bottom').grid
        y_visible = self.getAxis('left').grid
        self.showGrid(x=not x_visible, y=not y_visible)
        
    def _set_grid_alpha(self, alpha):
        """设置网格透明度"""
        self.showGrid(x=True, y=True, alpha=alpha)
        
    def _toggle_axes(self):
        """切换坐标轴显示"""
        for axis in ['left', 'bottom', 'right', 'top']:
            axis_item = self.getAxis(axis)
            axis_item.setVisible(not axis_item.isVisible())
            
    def _set_log_mode(self, axis, enabled):
        """设置对数模式"""
        if axis == 'x':
            self.setLogMode(x=enabled, y=None)
        else:
            self.setLogMode(x=None, y=enabled)


def apply_chinese_style_to_plot(plot_widget):
    """为现有的PlotWidget应用中文样式"""
    # 如果已经是中文化的部件，直接返回
    if isinstance(plot_widget, ChinesePlotWidget):
        return plot_widget
        
    # 为普通的PlotWidget添加中文菜单
    plot_widget.setMenuEnabled(False)
    
    def show_chinese_menu(event):
        if event.button() == Qt.MouseButton.RightButton:
            widget = ChinesePlotWidget()
            widget._show_chinese_context_menu(event.screenPos())
            
    plot_widget.scene().sigMouseClicked.connect(show_chinese_menu)
    return plot_widget