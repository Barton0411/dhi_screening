"""
进度条管理器模块
提供流畅的进度条显示和剩余时间估算
"""

import time
from typing import Optional, Callable
from PyQt6.QtWidgets import QProgressDialog, QApplication
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
import threading


class TimeEstimator:
    """时间估算器"""
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.start_time = None
        self.progress_history = []
        
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.progress_history = [(0, self.start_time)]
        
    def update(self, current_progress: float, total: float):
        """更新进度并返回剩余时间估算（秒）"""
        if not self.start_time or total == 0:
            return None
            
        current_time = time.time()
        progress_ratio = current_progress / total
        
        # 记录进度历史
        self.progress_history.append((progress_ratio, current_time))
        
        # 只保留最近的记录
        if len(self.progress_history) > self.window_size:
            self.progress_history.pop(0)
            
        # 计算速度（使用移动平均）
        if len(self.progress_history) < 2:
            return None
            
        # 计算平均速度
        time_delta = self.progress_history[-1][1] - self.progress_history[0][1]
        progress_delta = self.progress_history[-1][0] - self.progress_history[0][0]
        
        if progress_delta <= 0 or time_delta <= 0:
            return None
            
        speed = progress_delta / time_delta  # 进度/秒
        remaining_progress = 1.0 - progress_ratio
        
        if speed > 0:
            return remaining_progress / speed
        return None


class ProgressWorker(QObject):
    """后台工作线程"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, task_func: Callable, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
        
    def run(self):
        """执行任务"""
        try:
            # 添加进度回调
            self.kwargs['progress_callback'] = self.update_progress
            self.kwargs['status_callback'] = self.update_status
            self.kwargs['check_cancelled'] = lambda: self._is_cancelled
            
            result = self.task_func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
            
    def update_progress(self, value: int):
        """更新进度"""
        self.progress.emit(value)
        
    def update_status(self, text: str):
        """更新状态文本"""
        self.status.emit(text)
        
    def cancel(self):
        """取消任务"""
        self._is_cancelled = True


class SmoothProgressDialog(QProgressDialog):
    """流畅的进度对话框，支持剩余时间显示"""
    
    def __init__(self, title: str, cancel_text: str, minimum: int, maximum: int, parent=None):
        super().__init__(title, cancel_text, minimum, maximum, parent)
        
        self.time_estimator = TimeEstimator()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_time_display)
        
        self._current_value = minimum
        self._target_value = minimum
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._animate_progress)
        self._animation_timer.setInterval(16)  # 60 FPS
        
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumDuration(0)
        self.setAutoClose(False)
        self.setAutoReset(False)
        
        # 设置样式
        self.setStyleSheet("""
            QProgressDialog {
                min-width: 400px;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        
    def show(self):
        """显示对话框并开始计时"""
        super().show()
        self.time_estimator.start()
        self.update_timer.start(1000)  # 每秒更新一次时间显示
        self._animation_timer.start()
        
    def setValue(self, value: int):
        """设置目标进度值（带动画）"""
        self._target_value = value
        self.time_estimator.update(value, self.maximum())
        
    def _animate_progress(self):
        """动画更新进度条"""
        if self._current_value < self._target_value:
            # 计算步进值，确保动画流畅
            step = max(1, int((self._target_value - self._current_value) * 0.1))
            self._current_value = min(self._current_value + step, self._target_value)
            super().setValue(self._current_value)
        elif self._current_value > self._target_value:
            self._current_value = self._target_value
            super().setValue(self._current_value)
            
    def _update_time_display(self):
        """更新剩余时间显示"""
        remaining_seconds = self.time_estimator.update(self._current_value, self.maximum())
        
        if remaining_seconds is not None:
            if remaining_seconds < 60:
                time_str = f"剩余时间: {int(remaining_seconds)}秒"
            elif remaining_seconds < 3600:
                minutes = int(remaining_seconds / 60)
                seconds = int(remaining_seconds % 60)
                time_str = f"剩余时间: {minutes}分{seconds}秒"
            else:
                hours = int(remaining_seconds / 3600)
                minutes = int((remaining_seconds % 3600) / 60)
                time_str = f"剩余时间: {hours}小时{minutes}分"
                
            current_label = self.labelText()
            if " - 剩余时间:" in current_label:
                base_label = current_label.split(" - 剩余时间:")[0]
            else:
                base_label = current_label
            self.setLabelText(f"{base_label} - {time_str}")
            
    def close(self):
        """关闭对话框"""
        self.update_timer.stop()
        self._animation_timer.stop()
        super().close()


class AsyncProgressManager:
    """异步进度管理器"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.worker = None
        self.thread = None
        self.progress_dialog = None
        
    def execute_with_progress(self, 
                            task_func: Callable,
                            title: str = "处理中...",
                            cancel_text: str = "取消",
                            total_steps: int = 100,
                            *args, **kwargs) -> Optional[any]:
        """
        执行带进度条的异步任务
        
        Args:
            task_func: 要执行的任务函数
            title: 进度条标题
            cancel_text: 取消按钮文本
            total_steps: 总步骤数
            *args, **kwargs: 传递给任务函数的参数
            
        Returns:
            任务执行结果
        """
        # 创建进度对话框
        self.progress_dialog = SmoothProgressDialog(
            title, cancel_text, 0, total_steps, self.parent
        )
        
        # 创建工作线程
        self.thread = QThread()
        self.worker = ProgressWorker(task_func, *args, **kwargs)
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_dialog.setValue)
        self.worker.status.connect(self.progress_dialog.setLabelText)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.progress_dialog.canceled.connect(self._on_cancelled)
        
        # 用于存储结果
        self.result = None
        self.error = None
        self.finished = False
        
        # 启动
        self.progress_dialog.show()
        self.thread.start()
        
        # 事件循环，等待完成
        while not self.finished and self.progress_dialog.isVisible():
            QApplication.processEvents()
            time.sleep(0.01)
            
        # 清理
        self._cleanup()
        
        if self.error:
            raise Exception(self.error)
            
        return self.result
        
    def _on_finished(self, result):
        """任务完成处理"""
        self.result = result
        self.finished = True
        self.progress_dialog.close()
        
    def _on_error(self, error_msg):
        """错误处理"""
        self.error = error_msg
        self.finished = True
        self.progress_dialog.close()
        
    def _on_cancelled(self):
        """取消处理"""
        if self.worker:
            self.worker.cancel()
        self.finished = True
        
    def _cleanup(self):
        """清理资源"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
            
        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()
        if self.progress_dialog:
            self.progress_dialog.deleteLater()


def create_progress_dialog(parent, title: str = "处理中...", 
                         cancel_text: str = "取消", 
                         minimum: int = 0, 
                         maximum: int = 100) -> SmoothProgressDialog:
    """
    创建一个流畅的进度对话框
    
    Args:
        parent: 父窗口
        title: 标题
        cancel_text: 取消按钮文本
        minimum: 最小值
        maximum: 最大值
        
    Returns:
        SmoothProgressDialog实例
    """
    return SmoothProgressDialog(title, cancel_text, minimum, maximum, parent)