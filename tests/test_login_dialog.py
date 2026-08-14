import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from auth_module.login_dialog import LoginDialog


class FakeAuthService:
    username = None

    def __init__(self):
        self.saved_calls = []

    def load_credentials(self, auth_type=None):
        if auth_type == "yqn":
            return {
                "username": "remembered-user",
                "password": "remembered-password",
                "remember": True,
                "auth_type": "yqn",
            }
        return None

    def login_yqn(self, username, password):
        self.username = username
        return True, "登录成功", {"auth_type": "yqn"}

    def save_credentials(self, username, password, remember, auth_type):
        self.saved_calls.append((username, password, remember, auth_type))
        return True


class LoginDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_yqn_is_default_and_saved_password_is_loaded(self):
        service = FakeAuthService()
        dialog = LoginDialog(auth_service=service)

        self.assertEqual(dialog.login_type_combo.currentData(), "yqn")
        self.assertEqual(dialog.username_input.text(), "remembered-user")
        self.assertEqual(dialog.password_input.text(), "remembered-password")
        self.assertTrue(dialog.remember_checkbox.isChecked())
        self.assertTrue(dialog.remember_checkbox.isVisibleTo(dialog))

    def test_successful_yqn_login_saves_when_remember_is_checked(self):
        service = FakeAuthService()
        dialog = LoginDialog(auth_service=service)
        dialog._process_login("remembered-user", "remembered-password")

        self.assertEqual(
            service.saved_calls,
            [("remembered-user", "remembered-password", True, "yqn")],
        )


if __name__ == "__main__":
    unittest.main()
