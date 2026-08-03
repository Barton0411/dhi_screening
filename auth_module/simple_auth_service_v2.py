"""兼容旧导入路径；认证实现统一由 HTTPS 客户端提供。"""

from .simple_auth_service import SimpleAuthService

__all__ = ["SimpleAuthService"]
