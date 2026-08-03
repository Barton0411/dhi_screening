import tempfile
import unittest
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "auth_module" / "simple_auth_service.py"
SPEC = importlib.util.spec_from_file_location("simple_auth_service_under_test", MODULE_PATH)
AUTH_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUTH_MODULE)
SimpleAuthService = AUTH_MODULE.SimpleAuthService


class AuthServiceTests(unittest.TestCase):
    def make_service(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home = Path(temp_dir.name)
        patcher = patch("pathlib.Path.home", return_value=home)
        patcher.start()
        self.addCleanup(patcher.stop)
        return SimpleAuthService()

    def test_login_stores_token_and_profile(self):
        service = self.make_service()
        response = Mock(ok=True)
        response.json.return_value = {
            "success": True,
            "data": {"token": "synthetic-token", "name": "测试用户"},
        }
        service.session.request = Mock(return_value=response)

        success, message, extra = service.login("test-user", "synthetic-password")

        self.assertTrue(success)
        self.assertEqual(message, "登录成功")
        self.assertIsNone(extra)
        self.assertEqual(service.username, "test-user")
        self.assertEqual(service.get_user_name(), "测试用户")

    def test_invalid_auth_host_is_rejected(self):
        with self.assertRaises(ValueError):
            SimpleAuthService("https://example.com")

    def test_change_password_uses_bearer_token_and_clears_saved_password(self):
        service = self.make_service()
        service.token = "synthetic-token"
        service.username = "test-user"
        service.save_credentials("test-user", "old-synthetic-password", True)
        response = Mock(ok=True)
        response.json.return_value = {"success": True, "message": "密码修改成功"}
        service.session.request = Mock(return_value=response)

        success, _ = service.change_password(
            "old-synthetic-password", "new-synthetic-password"
        )

        self.assertTrue(success)
        self.assertIsNone(service.load_credentials())
        headers = service.session.request.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer synthetic-token")
