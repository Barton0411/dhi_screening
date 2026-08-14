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


class MemoryCredentialStore:
    def __init__(self):
        self.passwords = {}

    def set_password(self, service, account, password):
        self.passwords[(service, account)] = password

    def get_password(self, service, account):
        return self.passwords.get((service, account))

    def delete_password(self, service, account):
        self.passwords.pop((service, account), None)


class AuthServiceTests(unittest.TestCase):
    def make_service(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home = Path(temp_dir.name)
        patcher = patch("pathlib.Path.home", return_value=home)
        patcher.start()
        self.addCleanup(patcher.stop)
        return SimpleAuthService(credential_store=MemoryCredentialStore())

    def test_login_stores_token_and_profile(self):
        service = self.make_service()
        response = Mock(ok=True)
        response.json.return_value = {
            "success": True,
            "data": {
                "token": "synthetic-token",
                "name": "测试用户",
                "must_change_password": True,
                "auth_type": "local",
            },
        }
        service.session.request = Mock(return_value=response)

        success, message, extra = service.login("test-user", "synthetic-password")

        self.assertTrue(success)
        self.assertEqual(message, "登录成功")
        self.assertEqual(extra["auth_type"], "local")
        self.assertEqual(service.username, "test-user")
        self.assertEqual(service.get_user_name(), "测试用户")
        self.assertTrue(service.must_change_password)
        self.assertTrue(extra["must_change_password"])

    def test_yqn_login_exchanges_token_without_saving_upstream_token(self):
        service = self.make_service()
        upstream_response = Mock(ok=True)
        upstream_response.json.return_value = {
            "code": 200,
            "data": {"access_token": "synthetic-yqn-token"},
        }
        upstream_session = Mock()
        upstream_session.post.return_value = upstream_response
        exchange_response = Mock(ok=True)
        exchange_response.json.return_value = {
            "success": True,
            "data": {
                "token": "synthetic-software-token",
                "user_id": "trusted-yqn-user",
                "auth_type": "yqn",
                "must_change_password": False,
            },
        }
        service.session.post = Mock(return_value=exchange_response)

        with patch.object(AUTH_MODULE.requests, "Session", return_value=upstream_session):
            success, message, extra = service.login_yqn(
                "typed-user", "synthetic-password"
            )

        self.assertTrue(success)
        self.assertEqual(message, "登录成功")
        self.assertEqual(service.username, "trusted-yqn-user")
        self.assertEqual(service.token, "synthetic-software-token")
        self.assertEqual(service.auth_type, "yqn")
        self.assertFalse(extra["must_change_password"])
        exchange_headers = service.session.post.call_args.kwargs["headers"]
        self.assertEqual(
            exchange_headers["Authorization"], "Bearer synthetic-yqn-token"
        )

    def test_invalid_auth_host_is_rejected(self):
        with self.assertRaises(ValueError):
            SimpleAuthService("https://example.com")

    def test_change_password_uses_bearer_token_and_clears_saved_password(self):
        service = self.make_service()
        service.token = "synthetic-token"
        service.username = "test-user"
        service.save_credentials("test-user", "old-synthetic-password", True)
        response = Mock(ok=True)
        response.json.return_value = {
            "success": True,
            "message": "密码修改成功",
            "data": {"token": "replacement-token"},
        }
        service.session.request = Mock(return_value=response)

        success, _ = service.change_password(
            "old-synthetic-password", "new-synthetic-password"
        )

        self.assertTrue(success)
        self.assertEqual(service.token, "replacement-token")
        self.assertIsNone(service.load_credentials())
        headers = service.session.request.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer synthetic-token")

    def test_yqn_password_is_stored_only_in_system_credential_store(self):
        service = self.make_service()

        saved = service.save_credentials(
            "test-yqn-user", "synthetic-password", True, "yqn"
        )

        self.assertTrue(saved)
        self.assertEqual(
            service.load_credentials("yqn"),
            {
                "username": "test-yqn-user",
                "password": "synthetic-password",
                "remember": True,
                "auth_type": "yqn",
            },
        )
        metadata = service._credential_metadata_path().read_text(encoding="utf-8")
        self.assertNotIn("synthetic-password", metadata)
        self.assertFalse(
            (service._credential_metadata_path().parent / "credentials.enc").exists()
        )

    def test_credentials_are_scoped_to_login_type(self):
        service = self.make_service()
        service.save_credentials("test-yqn-user", "synthetic-password", True, "yqn")

        self.assertIsNone(service.load_credentials("local"))
        self.assertIsNotNone(service.load_credentials("yqn"))
