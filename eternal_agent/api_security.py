"""
阶段102：API 认证与安全
提供完整的 API 安全防护功能
"""
import re
import hashlib
import time
import secrets
import threading
from typing import Dict, List, Any, Optional, Set
from html import escape
from urllib.parse import urlparse

from .utils import logger, get_timestamp


class InputSanitizer:
    """
    输入验证与清理器
    提供XSS防护、输入验证、类型检查
    """
    
    # 禁止的字符模式
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'document\.',
        r'window\.',
        r'alert\s*\(',
    ]
    
    # 允许的字符集
    SAFE_NODE_NAME_CHARS = re.compile(r'^[a-zA-Z0-9_\-\s\.]+$')
    
    # 安全的属性键
    SAFE_ATTRIBUTE_KEYS = re.compile(r'^[a-zA-Z0-9_\-]+$')
    
    def __init__(self):
        self.dangerous_regex = re.compile('|'.join(self.DANGEROUS_PATTERNS), re.IGNORECASE)
    
    def sanitize_string(self, s: str, max_length: int = 1000) -> str:
        """清理字符串，防止XSS"""
        if not isinstance(s, str):
            return str(s)
        
        # 转义HTML
        s = escape(s)
        
        # 移除危险模式
        s = self.dangerous_regex.sub('', s)
        
        # 限制长度
        return s[:max_length]
    
    def validate_node_name(self, name: str) -> tuple[bool, str]:
        """验证节点名"""
        if not name or not isinstance(name, str):
            return False, "节点名必须为非空字符串"
        
        if len(name) > 200:
            return False, "节点名过长（最多200字符）"
        
        if not self.SAFE_NODE_NAME_CHARS.match(name):
            return False, "节点名包含非法字符"
        
        return True, ""
    
    def validate_attribute_key(self, key: str) -> tuple[bool, str]:
        """验证属性键"""
        if not key or not isinstance(key, str):
            return False, "属性键必须为非空字符串"
        
        if len(key) > 100:
            return False, "属性键过长（最多100字符）"
        
        if not self.SAFE_ATTRIBUTE_KEYS.match(key):
            return False, "属性键包含非法字符"
        
        return True, ""
    
    def sanitize_attributes(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """清理属性字典"""
        if not attrs or not isinstance(attrs, dict):
            return {}
        
        sanitized = {}
        for key, value in attrs.items():
            key_valid, key_msg = self.validate_attribute_key(key)
            if not key_valid:
                logger.warning(f"[Security] Invalid attribute key: {key}")
                continue
            
            if isinstance(value, str):
                sanitized[key] = self.sanitize_string(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        
        return sanitized
    
    def validate_tags(self, tags: List[str]) -> tuple[bool, str, List[str]]:
        """验证标签列表"""
        if not tags:
            return True, "", []
        
        if not isinstance(tags, list):
            return False, "标签必须是列表", []
        
        valid_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                continue
            tag = tag.strip()
            if len(tag) > 50:
                continue
            valid_tags.append(self.sanitize_string(tag, 50))
        
        return True, "", valid_tags[:20]


class CSRFProtection:
    """
    CSRF 防护
    生成和验证CSRF令牌
    """
    
    def __init__(self, token_ttl: int = 3600):
        self.token_ttl = token_ttl
        self.tokens: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def generate_token(self, session_id: str = None) -> str:
        """生成CSRF令牌"""
        with self._lock:
            token = secrets.token_urlsafe(32)
            self.tokens[token] = time.time() + self.token_ttl
            if session_id:
                self.tokens[f"{session_id}:{token}"] = time.time() + self.token_ttl
            return token
    
    def validate_token(self, token: str, session_id: str = None) -> bool:
        """验证CSRF令牌"""
        with self._lock:
            now = time.time()
            
            # 清理过期令牌
            self.tokens = {
                k: v for k, v in self.tokens.items() if v > now
            }
            
            if token in self.tokens:
                del self.tokens[token]
                return True
            
            if session_id:
                combined = f"{session_id}:{token}"
                if combined in self.tokens:
                    del self.tokens[combined]
                    return True
            
            return False


class Permission:
    """权限常量"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    READ_ONLY = "read_only"
    
    # 按HTTP方法映射权限
    METHOD_PERMISSIONS = {
        "GET": READ,
        "POST": WRITE,
        "PUT": WRITE,
        "DELETE": DELETE,
        "PATCH": WRITE
    }


class Role:
    """角色定义"""
    ADMIN = {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN}
    EDITOR = {Permission.READ, Permission.WRITE}
    VIEWER = {Permission.READ}
    READ_ONLY = {Permission.READ_ONLY}


class EnhancedAPIAuthenticator:
    """
    增强的API认证器
    支持API密钥、权限控制、密钥轮换
    """
    
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}
        self.revoked_keys: Set[str] = set()
        self.key_usage: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        
        # 权限到路径的映射
        self.path_permissions = {
            "/api/backup": Permission.ADMIN,
            "/api/maintenance": Permission.ADMIN,
            "/api/keys": Permission.ADMIN,
        }
    
    def add_api_key(self, key: str, name: str, 
                   permissions: Set[str] = None,
                   expires_at: float = None):
        """添加API密钥"""
        with self._lock:
            if permissions is None:
                permissions = Role.EDITOR
            
            self.api_keys[key] = {
                "name": name,
                "permissions": set(permissions),
                "created_at": get_timestamp(),
                "expires_at": expires_at,
                "last_used": None
            }
            self.key_usage[key] = []
            logger.info(f"[Security] Added API key for: {name}")
    
    def generate_key(self, name: str, 
                    permissions: Set[str] = None,
                    expires_in: int = None) -> str:
        """生成新的API密钥"""
        key = secrets.token_urlsafe(48)
        expires_at = None
        if expires_in:
            expires_at = time.time() + expires_in
        self.add_api_key(key, name, permissions, expires_at)
        return key
    
    def revoke_key(self, key: str):
        """撤销API密钥"""
        with self._lock:
            if key in self.api_keys:
                self.revoked_keys.add(key)
                logger.warning(f"[Security] Revoked API key: {self.api_keys[key]['name']}")
    
    def validate_key(self, key: str, 
                    required_permission: str = None,
                    path: str = None) -> tuple[bool, str]:
        """
        验证API密钥
        
        Returns: (success, error_message)
        """
        with self._lock:
            now = time.time()
            
            # 检查是否撤销
            if key in self.revoked_keys:
                return False, "API密钥已撤销"
            
            # 检查密钥是否存在
            if key not in self.api_keys:
                return False, "无效的API密钥"
            
            key_data = self.api_keys[key]
            
            # 检查过期
            if key_data["expires_at"] and now > key_data["expires_at"]:
                return False, "API密钥已过期"
            
            # 更新使用时间
            key_data["last_used"] = now
            self.key_usage[key].append(now)
            if len(self.key_usage[key]) > 1000:
                self.key_usage[key] = self.key_usage[key][-1000:]
            
            # 检查路径权限
            if path:
                for p, perm in self.path_permissions.items():
                    if path.startswith(p):
                        if perm not in key_data["permissions"]:
                            return False, f"权限不足（需要: {perm}）"
                        break
            
            # 检查所需权限
            if required_permission:
                if required_permission not in key_data["permissions"]:
                    return False, f"权限不足（需要: {required_permission}）"
            
            return True, ""
    
    def get_key_info(self, key: str) -> Optional[Dict]:
        """获取密钥信息（不带密钥值）"""
        with self._lock:
            if key not in self.api_keys:
                return None
            data = dict(self.api_keys[key])
            return data


class SecurityResponseHeaders:
    """安全响应头"""
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """获取安全响应头"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": "default-src 'self'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }


class SecurityAuditLog:
    """安全审计日志"""
    
    def __init__(self, max_logs: int = 10000):
        self.max_logs = max_logs
        self.logs: List[Dict] = []
        self._lock = threading.Lock()
    
    def log_event(self, event_type: str, details: Dict[str, Any] = None):
        """记录安全事件"""
        with self._lock:
            self.logs.append({
                "timestamp": get_timestamp(),
                "type": event_type,
                "details": details or {}
            })
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
    
    def get_logs(self, limit: int = 100) -> List[Dict]:
        """获取最近的安全日志"""
        with self._lock:
            return self.logs[-limit:]


# 全局实例
sanitizer = InputSanitizer()
csrf_protection = CSRFProtection()
security_audit = SecurityAuditLog()
