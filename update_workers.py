from PyQt6.QtCore import QThread, pyqtSignal

from update_manager import download_installer, fetch_update_manifest, is_newer_version
from version import get_version


class UpdateCheckWorker(QThread):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def run(self):
        try:
            manifest = fetch_update_manifest()
            self.completed.emit(
                manifest if is_newer_version(manifest["version"], get_version()) else None
            )
        except Exception:
            self.failed.emit("暂时无法连接更新服务")


class UpdateDownloadWorker(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, manifest: dict, parent=None):
        super().__init__(parent)
        self.manifest = manifest

    def run(self):
        try:
            path = download_installer(self.manifest, self.progress.emit)
            self.completed.emit(str(path))
        except Exception:
            self.failed.emit("更新包下载或校验失败，请稍后重试")
