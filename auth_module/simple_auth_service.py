"""HTTPS 认证客户端。

桌面应用只调用受控认证 API，不持有或连接生产数据库凭据。
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import requests
import certifi
from cryptography.fernet import Fernet, InvalidToken
import keyring


DEFAULT_AUTH_API_BASE_URL = "https://api.genepop.com"
ALLOWED_AUTH_HOSTS = {"api.genepop.com"}
YQN_LOGIN_URL = "https://yqnapi.yqndairy.com/auth/login"
REQUEST_TIMEOUT = (5, 15)
CREDENTIAL_SERVICE = "DHI Screening Assistant"
CREDENTIAL_METADATA_VERSION = 1


class SimpleAuthService:
    """保持旧界面调用契约的 HTTPS 认证适配器。"""

    def __init__(self, base_url: Optional[str] = None, credential_store=None):
        self.base_url = self._validate_base_url(
            base_url or os.environ.get("PROTEIN_SCREENING_AUTH_API_URL", DEFAULT_AUTH_API_BASE_URL)
        )
        self.username: Optional[str] = None
        self.user_name: Optional[str] = None
        self.token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.auth_type: Optional[str] = None
        self.must_change_password = False
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.verify = certifi.where()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "dhi-screening-desktop",
            }
        )
        self.credential_store = credential_store or keyring
        self.cipher_suite = self._init_legacy_cipher()

    @staticmethod
    def _validate_base_url(value: str) -> str:
        parsed = urlparse(value.rstrip("/"))
        if (
            parsed.scheme != "https"
            or parsed.hostname not in ALLOWED_AUTH_HOSTS
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("认证服务地址无效")
        return value.rstrip("/")

    def _init_legacy_cipher(self) -> Optional[Fernet]:
        """仅用于迁移旧版本地加密文件，不再创建可与密文一同复制的密钥。"""
        key_file = Path.home() / ".protein_screening" / "key.key"
        if not key_file.exists():
            return None
        try:
            return Fernet(key_file.read_bytes())
        except (OSError, ValueError):
            logging.warning("旧版本地凭据密钥无法读取")
            return None

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict] = None,
        authenticated: bool = False,
    ) -> Tuple[bool, Dict]:
        headers = {"Content-Type": "application/json"}
        if authenticated:
            if not self.token:
                return False, {"message": "登录状态已失效，请重新登录"}
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = self.session.request(
                method,
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("invalid response")
            return response.ok, data
        except (requests.RequestException, ValueError):
            logging.warning("认证服务请求失败: endpoint=%s", endpoint)
            return False, {"message": "认证服务暂时不可用，请稍后重试"}

    def register(
        self, employee_id: str, password: str, invite_code: str, name: str
    ) -> Tuple[bool, str]:
        _, data = self._request(
            "POST",
            "/api/auth/register",
            {
                "employee_id": employee_id,
                "password": password,
                "invite_code": invite_code,
                "name": name,
            },
        )
        allowed = {
            "注册成功",
            "用户名已存在",
            "邀请码不存在",
            "邀请码已失效",
            "邀请码已过期",
            "邀请码使用次数已达上限",
        }
        message = data.get("message")
        if data.get("success") is True:
            return True, "注册成功"
        return False, message if message in allowed else "注册暂时失败，请稍后重试"

    def login(
        self, username: str, password: str, force: bool = False
    ) -> Tuple[bool, str, Optional[Dict]]:
        del force  # HTTPS API 不允许客户端操纵其他设备的会话。
        _, data = self._request(
            "POST",
            "/api/auth/login",
            {"username": username, "password": password},
        )
        response_data = data.get("data") if isinstance(data.get("data"), dict) else {}
        token = response_data.get("token")
        if data.get("success") is True and isinstance(token, str) and token:
            self.username = str(response_data.get("user_id") or username)
            self.user_name = response_data.get("name")
            self.token = token
            self.session_id = token
            self.auth_type = "local"
            self.must_change_password = response_data.get("must_change_password") is True
            return True, "登录成功", {
                "must_change_password": self.must_change_password,
                "auth_type": self.auth_type,
            }

        self.logout()
        if data.get("message") == "用户名或密码错误":
            return False, "账号或密码错误", None
        return False, "认证服务暂时不可用，请稍后重试", None

    def login_yqn(
        self, username: str, password: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """使用伊起牛账号登录，再换取本软件 JWT。"""
        yqn_session = requests.Session()
        yqn_session.trust_env = False
        yqn_session.verify = certifi.where()
        try:
            response = yqn_session.post(
                YQN_LOGIN_URL,
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            result = response.json()
            result_data = result.get("data") if isinstance(result, dict) else None
            yqn_token = result_data.get("access_token") if isinstance(result_data, dict) else None
            if str(result.get("code")) != "200" or not isinstance(yqn_token, str) or not yqn_token:
                self.logout()
                return False, "账号或密码错误", None

            exchange = self.session.post(
                f"{self.base_url}/api/auth/yqn/exchange",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {yqn_token}",
                },
                timeout=REQUEST_TIMEOUT,
            )
            exchange_data = exchange.json()
            software_data = (
                exchange_data.get("data")
                if isinstance(exchange_data, dict) and isinstance(exchange_data.get("data"), dict)
                else {}
            )
            software_token = software_data.get("token")
            if not exchange.ok or exchange_data.get("success") is not True or not software_token:
                self.logout()
                return False, "伊起牛登录授权失败，请稍后重试", None

            self.username = str(software_data.get("user_id") or username)
            self.user_name = self.username
            self.token = str(software_token)
            self.session_id = self.token
            self.auth_type = "yqn"
            self.must_change_password = False
            return True, "登录成功", {
                "must_change_password": False,
                "auth_type": "yqn",
            }
        except (requests.RequestException, ValueError):
            logging.warning("伊起牛登录请求失败")
            self.logout()
            return False, "伊起牛登录服务暂时不可用，请稍后重试", None

    def change_password(self, current_password: str, new_password: str) -> Tuple[bool, str]:
        _, data = self._request(
            "POST",
            "/api/auth/change-password",
            {
                "current_password": current_password,
                "new_password": new_password,
            },
            authenticated=True,
        )
        allowed = {
            "密码修改成功",
            "当前密码错误",
            "新密码不能与当前密码相同",
            "未登录，请先登录",
        }
        message = data.get("message")
        if data.get("success") is True:
            response_data = data.get("data") if isinstance(data.get("data"), dict) else {}
            replacement_token = response_data.get("token")
            if isinstance(replacement_token, str) and replacement_token:
                self.token = replacement_token
                self.session_id = replacement_token
            self.must_change_password = False
            self.clear_credentials()
            return True, "密码修改成功"
        return False, message if message in allowed else "密码修改失败，请稍后重试"

    def heartbeat(self) -> bool:
        if not self.token:
            return False
        _, data = self._request("POST", "/api/auth/verify", authenticated=True)
        if data.get("success") is True:
            return True
        self.logout()
        return False

    def logout(self):
        self.username = None
        self.user_name = None
        self.token = None
        self.session_id = None
        self.auth_type = None
        self.must_change_password = False

    @staticmethod
    def _credential_account(auth_type: str, username: str) -> str:
        return f"{auth_type}:{username}"

    @staticmethod
    def _credential_metadata_path() -> Path:
        return Path.home() / ".protein_screening" / "login_preferences.json"

    def _read_credential_metadata(self) -> Optional[Dict]:
        metadata_path = self._credential_metadata_path()
        if not metadata_path.exists():
            return None
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            if (
                isinstance(data, dict)
                and data.get("version") == CREDENTIAL_METADATA_VERSION
                and data.get("auth_type") in {"local", "yqn"}
                and isinstance(data.get("username"), str)
            ):
                return data
        except (OSError, ValueError, json.JSONDecodeError):
            logging.warning("登录偏好无法读取")
        return None

    def save_credentials(
        self,
        username: str,
        password: str,
        remember: bool = True,
        auth_type: str = "local",
    ) -> bool:
        """将密码保存到系统凭据库；磁盘只记录非敏感的登录偏好。"""
        if auth_type not in {"local", "yqn"} or not username:
            return False
        self.clear_credentials()
        if not remember:
            return True
        try:
            self.credential_store.set_password(
                CREDENTIAL_SERVICE,
                self._credential_account(auth_type, username),
                password,
            )
            metadata_path = self._credential_metadata_path()
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(
                json.dumps(
                    {
                        "version": CREDENTIAL_METADATA_VERSION,
                        "auth_type": auth_type,
                        "username": username,
                        "remember": True,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            metadata_path.chmod(0o600)
            return True
        except Exception:
            logging.warning("系统凭据库写入失败")
            self.clear_credentials()
            return False

    def _migrate_legacy_credentials(self) -> Optional[Dict]:
        credential_file = Path.home() / ".protein_screening" / "credentials.enc"
        if not credential_file.exists() or self.cipher_suite is None:
            return None
        try:
            decrypted = self.cipher_suite.decrypt(credential_file.read_bytes())
            data = json.loads(decrypted.decode("utf-8"))
            if (
                isinstance(data, dict)
                and data.get("remember") is True
                and data.get("username")
                and data.get("password")
                and self.save_credentials(
                    str(data["username"]),
                    str(data["password"]),
                    True,
                    "local",
                )
            ):
                credential_file.unlink(missing_ok=True)
                return {
                    "username": str(data["username"]),
                    "password": str(data["password"]),
                    "remember": True,
                    "auth_type": "local",
                }
        except (OSError, ValueError, json.JSONDecodeError, InvalidToken):
            logging.warning("旧版登录信息无法迁移")
        return None

    def load_credentials(self, auth_type: Optional[str] = None) -> Optional[Dict]:
        metadata = self._read_credential_metadata()
        if metadata is None:
            migrated = self._migrate_legacy_credentials()
            if migrated and (auth_type is None or migrated["auth_type"] == auth_type):
                return migrated
            return None
        if auth_type is not None and metadata["auth_type"] != auth_type:
            return None
        try:
            password = self.credential_store.get_password(
                CREDENTIAL_SERVICE,
                self._credential_account(metadata["auth_type"], metadata["username"]),
            )
        except Exception:
            logging.warning("系统凭据库读取失败")
            return None
        if not password:
            return None
        return {
            "username": metadata["username"],
            "password": password,
            "remember": True,
            "auth_type": metadata["auth_type"],
        }

    def clear_credentials(
        self, auth_type: Optional[str] = None, username: Optional[str] = None
    ) -> None:
        metadata = self._read_credential_metadata()
        target_type = auth_type or (metadata.get("auth_type") if metadata else None)
        target_username = username or (metadata.get("username") if metadata else None)
        if target_type and target_username:
            try:
                self.credential_store.delete_password(
                    CREDENTIAL_SERVICE,
                    self._credential_account(target_type, target_username),
                )
            except Exception:
                pass
        metadata_path = self._credential_metadata_path()
        if metadata is None or (
            (auth_type is None or metadata.get("auth_type") == auth_type)
            and (username is None or metadata.get("username") == username)
        ):
            metadata_path.unlink(missing_ok=True)

        # 旧版密文不再继续使用；清理不影响系统凭据库之外的数据。
        legacy_file = Path.home() / ".protein_screening" / "credentials.enc"
        legacy_file.unlink(missing_ok=True)
        legacy_key = Path.home() / ".protein_screening" / "key.key"
        legacy_key.unlink(missing_ok=True)

    def check_server_health(self) -> bool:
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                headers={"Accept": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            return response.ok
        except requests.RequestException:
            return False

    def get_user_name(self) -> Optional[str]:
        return self.user_name
