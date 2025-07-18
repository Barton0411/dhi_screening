"""
认证服务模块 - 处理用户登录、注册和会话管理
"""

import logging

# 禁用 urllib3 警告
import warnings
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')

import requests
import os
import uuid
import json
from pathlib import Path
from typing import Optional, Tuple, Dict
from cryptography.fernet import Fernet

# 禁用localhost的代理
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

class AuthService:
    """用户认证服务类"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        初始化认证服务
        
        Args:
            server_url: 会话管理服务器地址
        """
        self.server_url = server_url.rstrip('/')
        self.device_id = self._get_or_create_device_id()
        self.session_token = None
        self.username = None
        
        # 用于本地凭证加密
        self.cipher_suite = self._init_cipher()
        
    def _init_cipher(self) -> Fernet:
        """初始化加密器"""
        key_file = Path.home() / ".protein_screening" / "key.key"
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            key = key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            
        return Fernet(key)
    
    def _get_or_create_device_id(self) -> str:
        """获取或创建设备ID"""
        device_file = Path.home() / ".protein_screening" / "device_id"
        device_file.parent.mkdir(exist_ok=True)
        
        if device_file.exists():
            return device_file.read_text().strip()
        else:
            device_id = str(uuid.uuid4())
            device_file.write_text(device_id)
            return device_id
    
    def register(self, employee_id: str, password: str, invite_code: str, name: str) -> Tuple[bool, str]:
        """
        注册新用户
        
        Args:
            employee_id: 工号（作为登录账号）
            password: 密码
            invite_code: 邀请码
            name: 姓名
            
        Returns:
            (成功标志, 消息)
        """
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.post(
                f"{self.server_url}/register",
                json={
                    "username": employee_id,  # 使用工号作为用户名
                    "password": password,
                    "invite_code": invite_code,
                    "name": name
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["success"], data["message"]
            else:
                return False, f"服务器错误: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "无法连接到服务器，请检查网络连接"
        except requests.exceptions.Timeout:
            return False, "连接超时，请稍后重试"
        except Exception as e:
            logging.error(f"注册失败: {str(e)}")
            return False, f"注册失败: {str(e)}"
    
    def login(self, username: str, password: str, force: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            force: 是否强制登录（踢掉其他设备）
            
        Returns:
            (成功标志, 消息, 额外数据)
        """
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.post(
                f"{self.server_url}/login",
                json={
                    "username": username,
                    "password": password,
                    "device_id": self.device_id,
                    "force_login": force
                },
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data["success"]:
                    self.session_token = data["session_token"]
                    self.username = username
                    return True, data["message"], None
                else:
                    # 检查是否需要强制登录
                    if data.get("need_force_login"):
                        return False, data["message"], {
                            "need_force_login": True,
                            "existing_device": data.get("existing_device")
                        }
                    else:
                        return False, data["message"], None
            else:
                # 更详细的错误信息
                if response.status_code == 500:
                    return False, "服务器内部错误，请稍后重试", None
                elif response.status_code == 505:
                    return False, "HTTP版本不支持，请联系管理员", None
                else:
                    try:
                        error_data = response.json()
                        return False, error_data.get("detail", f"服务器错误: {response.status_code}"), None
                    except:
                        return False, f"服务器错误: {response.status_code}", None
                
        except requests.exceptions.ConnectionError:
            return False, "无法连接到服务器，请检查网络连接", None
        except requests.exceptions.Timeout:
            return False, "连接超时，请稍后重试", None
        except Exception as e:
            logging.error(f"登录失败: {str(e)}")
            return False, f"登录失败: {str(e)}", None
    
    def heartbeat(self) -> bool:
        """
        发送心跳
        
        Returns:
            是否成功
        """
        if not self.session_token or not self.username:
            return False
            
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.post(
                f"{self.server_url}/heartbeat",
                json={
                    "username": self.username,
                    "device_id": self.device_id,
                    "session_token": self.session_token
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data["success"] and data.get("need_relogin"):
                    # 会话失效，需要重新登录
                    self.session_token = None
                    self.username = None
                    return False
                return data["success"]
            else:
                return False
                
        except Exception as e:
            logging.error(f"心跳失败: {str(e)}")
            return False
    
    def logout(self):
        """登出"""
        if self.session_token and self.username:
            try:
                session = requests.Session()
                session.trust_env = False
                session.post(
                    f"{self.server_url}/logout",
                    params={
                        "username": self.username,
                        "device_id": self.device_id,
                        "session_token": self.session_token
                    },
                    timeout=5
                )
            except Exception as e:
                logging.error(f"登出失败: {str(e)}")
            finally:
                self.session_token = None
                self.username = None
    
    def save_credentials(self, username: str, password: str, remember: bool = True):
        """
        保存登录凭证
        
        Args:
            username: 用户名
            password: 密码
            remember: 是否记住密码
        """
        cred_file = Path.home() / ".protein_screening" / "credentials.enc"
        
        if remember:
            data = {
                "username": username,
                "password": password,
                "remember": True
            }
            encrypted = self.cipher_suite.encrypt(json.dumps(data).encode())
            cred_file.write_bytes(encrypted)
        else:
            # 只保存用户名
            data = {
                "username": username,
                "password": "",
                "remember": False
            }
            encrypted = self.cipher_suite.encrypt(json.dumps(data).encode())
            cred_file.write_bytes(encrypted)
    
    def load_credentials(self) -> Optional[Dict[str, str]]:
        """
        加载保存的凭证
        
        Returns:
            凭证信息或None
        """
        cred_file = Path.home() / ".protein_screening" / "credentials.enc"
        
        if cred_file.exists():
            try:
                encrypted = cred_file.read_bytes()
                decrypted = self.cipher_suite.decrypt(encrypted)
                return json.loads(decrypted.decode())
            except Exception as e:
                logging.error(f"加载凭证失败: {str(e)}")
                return None
        return None
    
    def clear_credentials(self):
        """清除保存的凭证"""
        cred_file = Path.home() / ".protein_screening" / "credentials.enc"
        if cred_file.exists():
            cred_file.unlink()
    
    def check_server_health(self) -> bool:
        """
        检查服务器健康状态
        
        Returns:
            服务器是否可用
        """
        try:
            # 创建不使用代理的session
            session = requests.Session()
            session.trust_env = False
            response = session.get(f"{self.server_url}/health", timeout=3)
            return response.status_code == 200
        except Exception as e:
            logging.debug(f"健康检查失败: {e}")
            return False