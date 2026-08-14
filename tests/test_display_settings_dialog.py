import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QScrollArea

from desktop_app import DisplaySettingsDialog


class DisplaySettingsDialogTests(unittest.TestCase):
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

    def test_dialog_uses_compact_non_scrolling_layout(self):
        dialog = DisplaySettingsDialog()
        dialog.show()
        self.app.processEvents()

        self.assertFalse(dialog.findChildren(QScrollArea))
        self.assertLessEqual(dialog.minimumHeight(), 600)
        self.assertEqual(
            [dialog.scale_combo.itemData(i) for i in range(dialog.scale_combo.count())],
            [90, 100, 110, 125],
        )
        self.assertEqual(
            [dialog.theme_combo.itemData(i) for i in range(dialog.theme_combo.count())],
            ["system", "light", "dark"],
        )


if __name__ == "__main__":
    unittest.main()
