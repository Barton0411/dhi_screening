import importlib.util
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

MODULE_PATH = Path(__file__).resolve().parents[1] / "auth_module" / "change_password_dialog.py"
SPEC = importlib.util.spec_from_file_location("change_password_dialog", MODULE_PATH)
CHANGE_PASSWORD_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHANGE_PASSWORD_MODULE)
ChangePasswordDialog = CHANGE_PASSWORD_MODULE.ChangePasswordDialog


class ChangePasswordDialogLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_required_dialog_keeps_all_controls_inside_visible_area(self):
        dialog = ChangePasswordDialog(username="测试账号", required=True)
        dialog.show()
        self.app.processEvents()

        controls = [
            dialog.title_label,
            dialog.user_label,
            dialog.old_password_label,
            dialog.old_password_input,
            dialog.new_password_label,
            dialog.new_password_input,
            dialog.confirm_password_label,
            dialog.confirm_password_input,
            dialog.change_btn,
        ]

        for control in controls:
            self.assertTrue(control.isVisible())
            bottom_right = control.mapTo(dialog, control.rect().bottomRight())
            self.assertLessEqual(bottom_right.x(), dialog.contentsRect().right())
            self.assertLessEqual(bottom_right.y(), dialog.contentsRect().bottom())

        self.assertGreater(
            dialog.old_password_input.geometry().top(),
            dialog.old_password_label.geometry().bottom(),
        )
        self.assertGreater(
            dialog.new_password_input.geometry().top(),
            dialog.new_password_label.geometry().bottom(),
        )
        self.assertGreater(
            dialog.confirm_password_input.geometry().top(),
            dialog.confirm_password_label.geometry().bottom(),
        )

        dialog.required = False
        dialog.close()


if __name__ == "__main__":
    unittest.main()
