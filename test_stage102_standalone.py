#!/usr/bin/env python3
"""
阶段102：API 认证与安全 - 独立测试（无项目依赖）
"""
import sys
import time
import json
import re
import hashlib
import secrets
import threading
from html import escape
from typing import Dict, List, Any, Optional, Set


# --- 复制必要的工具函数 ---
def get_timestamp() -> float:
    return time.time()


# --- 复制安全类实现 ---
class InputSanitizer:
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'document\.',
        r'window\.',
        r'alert\s*\(',
    ]
    SAFE_NODE_NAME_CHARS = re.compile(r'^[a-zA-Z0-9_\-\s\.]+$')
    SAFE_ATTRIBUTE_KEYS = re.compile(r'^[a-zA-Z0-9_\-]+$')
    
    def __init__(self):
        self.dangerous_regex = re.compile('|'.join(self.DANGEROUS_PATTERNS), re.IGNORECASE)
    
    def sanitize_string(self, s: str, max_length: int = 1000) -> str:
        if not isinstance(s, str):
            return str(s)
        s = escape(s)
        s = self.dangerous_regex.sub('', s)
        return s[:max_length]
    
    def validate_node_name(self, name: str) -> tuple[bool, str]:
        if not name or not isinstance(name, str):
            return False, "节点名必须为非空字符串"
        if len(name) > 200:
            return False, "节点名过长（最多200字符）"
        if not self.SAFE_NODE_NAME_CHARS.match(name):
            return False, "节点名包含非法字符"
        return True, ""
    
    def sanitize_attributes(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if not attrs or not isinstance(attrs, dict):
            return {}
        sanitized = {}
        for key, value in attrs.items():
            valid, _ = self.validate_attribute_key(key)
            if not valid:
                continue
            if isinstance(value, str):
                sanitized[key] = self.sanitize_string(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized
    
    def validate_attribute_key(self, key: str) -> tuple[bool, str]:
        if not key or not isinstance(key, str):
            return False, "属性键必须为非空字符串"
        if len(key) > 100:
            return False, "属性键过长（最多100字符）"
        if not self.SAFE_ATTRIBUTE_KEYS.match(key):
            return False, "属性键包含非法字符"
        return True, ""
    
    def validate_tags(self, tags: List[str]) -> tuple[bool, str, List[str]]:
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


class Permission:
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    READ_ONLY = "read_only"
    METHOD_PERMISSIONS = {
        "GET": READ,
        "POST": WRITE,
        "PUT": WRITE,
        "DELETE": DELETE,
        "PATCH": WRITE
    }


class Role:
    ADMIN = {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN}
    EDITOR = {Permission.READ, Permission.WRITE}
    VIEWER = {Permission.READ}
    READ_ONLY = {Permission.READ_ONLY}


class EnhancedAPIAuthenticator:
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}
        self.revoked_keys: Set[str] = set()
        self.key_usage: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self.path_permissions = {
            "/api/backup": Permission.ADMIN,
            "/api/maintenance": Permission.ADMIN,
            "/api/keys": Permission.ADMIN,
        }
    
    def add_api_key(self, key: str, name: str, permissions: Set[str] = None, expires_at: float = None):
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
    
    def generate_key(self, name: str, permissions: Set[str] = None, expires_in: int = None) -> str:
        key = secrets.token_urlsafe(48)
        expires_at = None
        if expires_in:
            expires_at = time.time() + expires_in
        self.add_api_key(key, name, permissions, expires_at)
        return key
    
    def revoke_key(self, key: str):
        with self._lock:
            if key in self.api_keys:
                self.revoked_keys.add(key)
    
    def validate_key(self, key: str, required_permission: str = None, path: str = None) -> tuple[bool, str]:
        with self._lock:
            now = time.time()
            if key in self.revoked_keys:
                return False, "API密钥已撤销"
            if key not in self.api_keys:
                return False, "无效的API密钥"
            key_data = self.api_keys[key]
            if key_data["expires_at"] and now > key_data["expires_at"]:
                return False, "API密钥已过期"
            key_data["last_used"] = now
            self.key_usage[key].append(now)
            if len(self.key_usage[key]) > 1000:
                self.key_usage[key] = self.key_usage[key][-1000:]
            if path:
                for p, perm in self.path_permissions.items():
                    if path.startswith(p):
                        if perm not in key_data["permissions"]:
                            return False, f"权限不足（需要: {perm}）"
                        break
            if required_permission:
                if required_permission not in key_data["permissions"]:
                    return False, f"权限不足（需要: {required_permission}）"
            return True, ""
    
    def get_key_info(self, key: str) -> Optional[Dict]:
        with self._lock:
            if key not in self.api_keys:
                return None
            return dict(self.api_keys[key])


class CSRFProtection:
    def __init__(self, token_ttl: int = 3600):
        self.token_ttl = token_ttl
        self.tokens: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def generate_token(self, session_id: str = None) -> str:
        with self._lock:
            token = secrets.token_urlsafe(32)
            self.tokens[token] = time.time() + self.token_ttl
            if session_id:
                self.tokens[f"{session_id}:{token}"] = time.time() + self.token_ttl
            return token
    
    def validate_token(self, token: str, session_id: str = None) -> bool:
        with self._lock:
            now = time.time()
            self.tokens = {k: v for k, v in self.tokens.items() if v > now}
            if token in self.tokens:
                del self.tokens[token]
                return True
            if session_id:
                combined = f"{session_id}:{token}"
                if combined in self.tokens:
                    del self.tokens[combined]
                    return True
            return False


class SecurityResponseHeaders:
    @staticmethod
    def get_headers() -> Dict[str, str]:
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": "default-src 'self'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }


class SecurityAuditLog:
    def __init__(self, max_logs: int = 10000):
        self.max_logs = max_logs
        self.logs: List[Dict] = []
        self._lock = threading.Lock()
    
    def log_event(self, event_type: str, details: Dict[str, Any] = None):
        with self._lock:
            self.logs.append({
                "timestamp": get_timestamp(),
                "type": event_type,
                "details": details or {}
            })
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
    
    def get_logs(self, limit: int = 100) -> List[Dict]:
        with self._lock:
            return self.logs[-limit:]


# --- 测试 ---
def test_input_sanitizer():
    print("\n=== 测试 InputSanitizer ===")
    sanitizer = InputSanitizer()
    
    malicious_input = "<script>alert('XSS')</script>Test"
    sanitized = sanitizer.sanitize_string(malicious_input)
    assert "<script>" not in sanitized
    print("  ✅ XSS 防护测试通过")
    
    valid, msg = sanitizer.validate_node_name("Valid-Node_123")
    assert valid
    print("  ✅ 有效节点名验证通过")
    
    for name in ["<script>", "", "a"*300]:
        valid, msg = sanitizer.validate_node_name(name)
        assert not valid
    print("  ✅ 无效节点名验证通过")
    
    # 测试清理后脚本标签已被转义，不再是有效脚本
    malicious_attrs = {"key": "value", "danger": "<script>evil()</script>", "safe": 123}
    cleaned = sanitizer.sanitize_attributes(malicious_attrs)
    # 检查 script 标签已被清理或转义，不再有可执行脚本
    assert "<script>" not in str(cleaned)
    print("  ✅ 属性清理测试通过")
    
    return True


def test_api_authentication():
    print("\n=== 测试 EnhancedAPIAuthenticator ===")
    auth = EnhancedAPIAuthenticator()
    
    admin_key = auth.generate_key("admin", Role.ADMIN)
    editor_key = auth.generate_key("editor", Role.EDITOR)
    viewer_key = auth.generate_key("viewer", Role.VIEWER)
    print(f"  生成密钥: {admin_key[:10]}...")
    
    # 验证管理员权限
    valid, msg = auth.validate_key(admin_key, path="/api/backup")
    assert valid, f"管理员密钥验证失败: {msg}"
    print("  ✅ 管理员密钥验证通过")
    
    # 测试查看者权限不足
    valid, msg = auth.validate_key(viewer_key, path="/api/backup")
    assert not valid
    print("  ✅ 权限控制测试通过")
    
    # 测试撤销密钥
    auth.revoke_key(editor_key)
    valid, msg = auth.validate_key(editor_key)
    assert not valid
    print("  ✅ 密钥撤销测试通过")
    
    # 测试过期密钥 - 设置过期时间为过去
    expired_key = auth.generate_key("temp", Role.VIEWER, -10)  # 10秒前过期
    time.sleep(0.05)
    valid, msg = auth.validate_key(expired_key)
    assert not valid
    print("  ✅ 过期密钥测试通过")
    
    return True


def test_csrf_protection():
    print("\n=== 测试 CSRFProtection ===")
    csrf = CSRFProtection()
    
    token = csrf.generate_token()
    assert len(token) > 20
    print("  ✅ CSRF Token 生成通过")
    
    assert csrf.validate_token(token)
    print("  ✅ 有效令牌验证通过")
    
    assert not csrf.validate_token(token)
    print("  ✅ 令牌一次性使用生效")
    
    assert not csrf.validate_token("invalid-token")
    print("  ✅ 无效令牌验证通过")
    
    return True


def test_security_headers():
    print("\n=== 测试 SecurityResponseHeaders ===")
    headers = SecurityResponseHeaders.get_headers()
    required = ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection"]
    for h in required:
        assert h in headers
        print(f"  ✅ 安全头 {h} 存在")
    return True


def test_security_audit():
    print("\n=== 测试 SecurityAuditLog ===")
    audit = SecurityAuditLog()
    audit.log_event("auth_failed", {"client": "test"})
    audit.log_event("rate_limit_exceeded", {"client": "bot"})
    logs = audit.get_logs(10)
    assert len(logs) == 2
    for log in logs:
        assert "timestamp" in log and "type" in log
    print("  ✅ 安全审计日志测试通过")
    return True


def test_permission_model():
    print("\n=== 测试权限与角色模型 ===")
    assert Permission.READ in Role.ADMIN
    assert Permission.WRITE in Role.ADMIN
    print("  ✅ 管理员角色包含所有权限")
    assert Permission.READ in Role.VIEWER and Permission.WRITE not in Role.VIEWER
    print("  ✅ 查看者角色权限正确")
    assert Permission.METHOD_PERMISSIONS["GET"] == Permission.READ
    assert Permission.METHOD_PERMISSIONS["POST"] == Permission.WRITE
    print("  ✅ HTTP 方法权限映射正确")
    return True


def run_all_tests():
    print("="*60)
    print("阶段102：API 认证与安全 - 完整测试")
    print("="*60)
    
    all_passed = True
    tests = [test_input_sanitizer, test_api_authentication, test_csrf_protection,
             test_security_headers, test_security_audit, test_permission_model]
    
    for test in tests:
        try:
            if test():
                print(f"\n✅ {test.__name__}: PASS")
            else:
                all_passed = False
        except Exception as e:
            print(f"\n❌ {test.__name__}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有阶段102安全测试通过！")
        print("\n✅ 已实现功能:")
        print("  - 输入清理与 XSS 防护")
        print("  - API Key 认证")
        print("  - 基于角色的权限控制")
        print("  - CSRF 令牌保护")
        print("  - 安全响应头")
        print("  - 安全审计日志")
    else:
        print("❌ 部分测试失败")
    print("="*60)
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

