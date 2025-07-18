# 认证模块
try:
    from .simple_auth_service import SimpleAuthService as AuthService
except ImportError:
    from .simple_auth_service_v2 import SimpleAuthService as AuthService

from .login_dialog import LoginDialog, show_login_dialog
from .register_dialog import RegisterDialog, show_register_dialog
from .forgot_password_dialog import ForgotPasswordDialog
from .change_password_dialog import ChangePasswordDialog
from .invite_code_dialog import InviteCodeDialog

__all__ = [
    'AuthService',
    'LoginDialog',
    'show_login_dialog',
    'RegisterDialog',
    'show_register_dialog',
    'ForgotPasswordDialog',
    'ChangePasswordDialog',
    'InviteCodeDialog'
]