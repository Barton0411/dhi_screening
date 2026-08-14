import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QLabel

from desktop_app import MainWindow
from version import get_version


class MainWindowUpdateUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            self.temp_dir.name,
        )
        self.window = MainWindow(username="test-user", auth_service=None)
        self.addCleanup(self.window.close)

    def test_header_shows_current_version_and_manual_update_button(self):
        version_label = self.window.findChild(QLabel, "versionLabel")
        self.assertIsNotNone(version_label)
        self.assertEqual(version_label.text(), f"v{get_version()}")
        self.assertEqual(self.window.check_update_btn.text(), "检查更新")

    def test_forced_manual_update_starts_download_without_skip_option(self):
        manifest = {
            "version": "9.99.99",
            "force_update": True,
            "changes": ["测试更新"],
        }
        with patch("desktop_app.QMessageBox.information"), patch.object(
            self.window, "_download_update"
        ) as download:
            self.window._handle_update_check_result(manifest)

        download.assert_called_once_with(manifest)


if __name__ == "__main__":
    unittest.main()
