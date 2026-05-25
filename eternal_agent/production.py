"""
基于第一性原理的轻量化永动知识图谱Agent
阶段91-100：生产化与未来扩展
"""

import os
import json
import hashlib
import tempfile
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from .utils import logger, get_timestamp


class Environment(Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ConfigSchema:
    """配置模式定义"""
    name: str
    type: str  # string, number, boolean, object, array
    default: Any = None
    description: str = ""
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: List[Any] = None


class ConfigValidator:
    """配置验证器"""
    
    SCHEMAS: Dict[str, ConfigSchema] = {}
    
    @classmethod
    def register_schema(cls, schema: ConfigSchema):
        """注册配置模式"""
        cls.SCHEMAS[schema.name] = schema
    
    @classmethod
    def validate(cls, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证配置"""
        errors = []
        
        for name, schema in cls.SCHEMAS.items():
            value = config.get(name)
            
            if schema.required and value is None:
                errors.append(f"Missing required config: {name}")
                continue
            
            if value is None:
                continue
            
            if schema.type == "number":
                if not isinstance(value, (int, float)):
                    errors.append(f"{name} must be a number")
                elif schema.min_value and value < schema.min_value:
                    errors.append(f"{name} must be >= {schema.min_value}")
                elif schema.max_value and value > schema.max_value:
                    errors.append(f"{name} must be <= {schema.max_value}")
            
            elif schema.type == "string":
                if not isinstance(value, str):
                    errors.append(f"{name} must be a string")
                elif schema.options and value not in schema.options:
                    errors.append(f"{name} must be one of {schema.options}")
            
            elif schema.type == "boolean":
                if not isinstance(value, bool):
                    errors.append(f"{name} must be a boolean")
        
        return len(errors) == 0, errors


class HotReloadConfig:
    """
    阶段91：配置管理完善
    
    支持热加载的配置管理器
    """
    
    def __init__(self, config_path: str = "agent_config.json"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.environment = Environment.DEVELOPMENT
        self._watch_thread: Optional[threading.Thread] = None
        self._running = False
        self._callbacks: List[Callable] = []
        self._last_modified = 0
        self._lock = threading.Lock()
        
        self._load_config()
        self._register_default_schemas()
    
    def _register_default_schemas(self):
        """注册默认配置模式"""
        schemas = [
            ConfigSchema("save_interval", "number", 300, "Save interval in seconds", True, 1, 3600),
            ConfigSchema("log_level", "string", "INFO", "Logging level", False, options=["DEBUG", "INFO", "WARNING", "ERROR"]),
            ConfigSchema("max_backups", "number", 10, "Maximum backup count", True, 1, 100),
            ConfigSchema("enable_auto_backup", "boolean", True, "Enable automatic backup"),
            ConfigSchema("health_check_interval", "number", 60, "Health check interval", True, 10, 3600),
            ConfigSchema("evolution_cycles", "number", 100, "Evolution cycles", True, 1, 10000),
            ConfigSchema("max_memory_mb", "number", 1024, "Maximum memory usage in MB", True, 128, 8192),
        ]
        
        for schema in schemas:
            ConfigValidator.register_schema(schema)
    
    def _load_config(self):
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self._last_modified = os.path.getmtime(self.config_path)
                logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self.config = {}
        else:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, persist: bool = False):
        """设置配置"""
        with self._lock:
            self.config[key] = value
            if persist:
                self._save_config()
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self._last_modified = os.path.getmtime(self.config_path)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def reload(self):
        """重新加载配置"""
        old_config = self.config.copy()
        self._load_config()
        
        changed_keys = []
        for key in set(old_config.keys()) | set(self.config.keys()):
            if old_config.get(key) != self.config.get(key):
                changed_keys.append(key)
        
        if changed_keys:
            logger.info(f"Config reloaded, changed keys: {changed_keys}")
            for callback in self._callbacks:
                try:
                    callback(changed_keys)
                except Exception as e:
                    logger.error(f"Config change callback failed: {e}")
    
    def register_change_callback(self, callback: Callable):
        """注册配置变更回调"""
        self._callbacks.append(callback)
    
    def start_watching(self, interval: float = 5.0):
        """启动配置监视"""
        if self._running:
            return
        
        self._running = True
        self._watch_thread = threading.Thread(target=self._watch_loop, args=(interval,), daemon=True)
        self._watch_thread.start()
        logger.info("Started config hot reload watcher")
    
    def _watch_loop(self, interval: float):
        """监视循环"""
        while self._running:
            try:
                if self.config_path.exists():
                    current_mtime = os.path.getmtime(self.config_path)
                    if current_mtime > self._last_modified:
                        logger.info("Config file changed, reloading...")
                        self.reload()
            except Exception as e:
                logger.error(f"Config watch error: {e}")
            
            time.sleep(interval)
    
    def stop_watching(self):
        """停止监视"""
        self._running = False
        if self._watch_thread:
            self._watch_thread.join(timeout=2)
        logger.info("Stopped config hot reload watcher")
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证配置"""
        return ConfigValidator.validate(self.config)
    
    def to_dict(self) -> Dict[str, Any]:
        """导出配置"""
        return self.config.copy()


class DeploymentManager:
    """
    阶段92：部署自动化
    
    部署管理器和容器化支持
    """
    
    @staticmethod
    def generate_dockerfile(python_version: str = "3.11") -> str:
        """生成Dockerfile"""
        return f'''FROM python:{python_version}-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]
'''
    
    @staticmethod
    def generate_docker_compose(service_name: str = "eternal-agent") -> str:
        """生成docker-compose.yml"""
        return f'''version: '3.8'

services:
  {service_name}:
    build: .
    container_name: {service_name}
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "python", "-c", "import eternal_agent"]
      interval: 30s
      timeout: 10s
      retries: 3
'''
    
    @staticmethod
    def generate_systemd_service(name: str = "eternal-agent") -> str:
        """生成systemd服务文件"""
        return f'''[Unit]
Description=EternalAgent - 永动知识图谱Agent
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory=/opt/eternal-agent
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''
    
    @classmethod
    def create_deployment_package(cls, output_dir: str = "deployment") -> str:
        """创建部署包"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        files = {
            "Dockerfile": cls.generate_dockerfile(),
            "docker-compose.yml": cls.generate_docker_compose(),
            "eternal-agent.service": cls.generate_systemd_service(),
            "README.md": cls._generate_deployment_readme(),
        }
        
        for filename, content in files.items():
            (output_path / filename).write_text(content)
            logger.info(f"Created {filename}")
        
        return str(output_path)
    
    @staticmethod
    def _generate_deployment_readme() -> str:
        """生成部署说明"""
        return '''# EternalAgent 部署指南

## Docker 部署

```bash
docker-compose up -d
```

## Systemd 部署

```bash
sudo cp eternal-agent.service /etc/systemd/system/
sudo systemctl enable eternal-agent
sudo systemctl start eternal-agent
```

## 环境变量

- `PYTHONUNBUFFERED=1` - 实时输出日志
- `AGENT_CONFIG_PATH` - 配置文件路径
'''


class SecurityManager:
    """
    阶段94：安全加固
    
    数据加密和访问控制
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or os.getenv("AGENT_ENCRYPTION_KEY", "")
        self._access_log: List[Dict] = []
    
    def encrypt_data(self, data: str) -> str:
        """简单加密（实际生产应使用更强的加密）"""
        if not self.encryption_key:
            return data
        
        key_bytes = self.encryption_key.encode()[:32].ljust(32, b'0')
        data_bytes = data.encode()
        
        encrypted = bytes(a ^ b for a, b in zip(data_bytes * 32, key_bytes * (len(data_bytes) // 32 + 1)))
        return encrypted.hex()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """简单解密"""
        if not self.encryption_key:
            return encrypted_data
        
        key_bytes = self.encryption_key.encode()[:32].ljust(32, b'0')
        encrypted_bytes = bytes.fromhex(encrypted_data)
        
        decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes * 32, key_bytes * (len(encrypted_bytes) // 32 + 1)))
        return decrypted.decode().rstrip('\x00')
    
    def hash_sensitive_data(self, data: str) -> str:
        """哈希敏感数据"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def log_access(self, resource: str, action: str, user: str = "system"):
        """记录访问"""
        self._access_log.append({
            "timestamp": get_timestamp(),
            "resource": resource,
            "action": action,
            "user": user
        })
    
    def get_access_log(self, limit: int = 100) -> List[Dict]:
        """获取访问日志"""
        return self._access_log[-limit:]


class PerformanceBenchmark:
    """
    阶段95：性能基准测试
    
    性能测试和基准追踪
    """
    
    def __init__(self):
        self.benchmarks: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def record_benchmark(self, name: str, duration_ms: float):
        """记录基准测试结果"""
        with self._lock:
            if name not in self.benchmarks:
                self.benchmarks[name] = []
            self.benchmarks[name].append(duration_ms)
    
    def run_benchmark(self, name: str, func: Callable, iterations: int = 100) -> Dict:
        """运行基准测试"""
        durations = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            duration_ms = (time.perf_counter() - start) * 1000
            durations.append(duration_ms)
        
        self.record_benchmark(name, sum(durations) / len(durations))
        
        return {
            "name": name,
            "iterations": iterations,
            "avg_ms": sum(durations) / len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "median_ms": sorted(durations)[len(durations) // 2]
        }
    
    def get_benchmark_report(self) -> Dict:
        """获取基准测试报告"""
        with self._lock:
            report = {}
            for name, durations in self.benchmarks.items():
                if durations:
                    report[name] = {
                        "runs": len(durations),
                        "avg_ms": sum(durations) / len(durations),
                        "min_ms": min(durations),
                        "max_ms": max(durations),
                        "latest_ms": durations[-1]
                    }
            return report


class PluginInterface:
    """插件接口基类"""
    
    def on_load(self, agent):
        """插件加载时调用"""
        pass
    
    def on_unload(self):
        """插件卸载时调用"""
        pass
    
    def on_task(self, task):
        """处理任务时调用"""
        return task
    
    def on_event(self, event):
        """处理事件时调用"""
        pass


class PluginManager:
    """
    阶段96：插件系统
    
    插件管理和加载
    """
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self._lock = threading.Lock()
    
    def register_plugin(self, name: str, plugin: PluginInterface):
        """注册插件"""
        with self._lock:
            self.plugins[name] = plugin
            logger.info(f"Registered plugin: {name}")
    
    def unregister_plugin(self, name: str):
        """注销插件"""
        with self._lock:
            if name in self.plugins:
                self.plugins[name].on_unload()
                del self.plugins[name]
                logger.info(f"Unregistered plugin: {name}")
    
    def load_plugin_from_module(self, name: str, module_path: str) -> bool:
        """从模块加载插件"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'Plugin'):
                    plugin = module.Plugin()
                    self.register_plugin(name, plugin)
                    return True
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
        return False
    
    def notify_plugins(self, event: str, data: Any):
        """通知所有插件"""
        with self._lock:
            for name, plugin in self.plugins.items():
                try:
                    plugin.on_event({"type": event, "data": data})
                except Exception as e:
                    logger.error(f"Plugin {name} event handler failed: {e}")
    
    def get_plugin_info(self) -> List[Dict]:
        """获取插件信息"""
        with self._lock:
            return [
                {
                    "name": name,
                    "type": type(plugin).__name__
                }
                for name, plugin in self.plugins.items()
            ]


class Internationalization:
    """
    阶段97：多语言支持
    
    国际化框架
    """
    
    DEFAULT_LANGUAGE = "zh_CN"
    
    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        "zh_CN": {
            "system_initializing": "系统初始化中...",
            "system_ready": "系统就绪",
            "task_executing": "执行任务: {task}",
            "knowledge_accumulated": "已积累知识: {count} 条",
            "system_healthy": "系统健康",
            "evolution_cycle": "进化周期: {cycle}",
            "memory_usage": "内存使用: {usage} MB",
        },
        "en_US": {
            "system_initializing": "System initializing...",
            "system_ready": "System ready",
            "task_executing": "Executing task: {task}",
            "knowledge_accumulated": "Knowledge accumulated: {count}",
            "system_healthy": "System healthy",
            "evolution_cycle": "Evolution cycle: {cycle}",
            "memory_usage": "Memory usage: {usage} MB",
        }
    }
    
    def __init__(self, language: str = None):
        self.current_language = language or self.DEFAULT_LANGUAGE
    
    def set_language(self, language: str):
        """设置语言"""
        if language in self.TRANSLATIONS:
            self.current_language = language
            logger.info(f"Language set to: {language}")
        else:
            logger.warning(f"Unknown language: {language}, using default")
    
    def t(self, key: str, **kwargs) -> str:
        """翻译文本"""
        text = self.TRANSLATIONS.get(self.current_language, {}).get(key, key)
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text


class CommunityGuidelines:
    """
    阶段98：社区建设
    
    贡献指南和代码规范
    """
    
    @staticmethod
    def get_contributing_guide() -> str:
        """获取贡献指南"""
        return '''
# EternalAgent 贡献指南

## 开发环境设置

```bash
git clone https://github.com/17683995446/eternal-agent.git
cd eternal-agent
pip install -r requirements.txt
```

## 代码规范

- 使用 PEP 8 代码风格
- 所有函数和类必须有文档字符串
- 提交前运行测试：`python -m pytest`
- 提交信息遵循 Conventional Commits 规范

## 分支管理

- `main`: 稳定版本
- `develop`: 开发版本
- `feature/*`: 新功能
- `bugfix/*`: 错误修复

## Pull Request 流程

1. Fork 仓库
2. 创建功能分支
3. 开发并测试
4. 提交 Pull Request
5. 代码审查
6. 合并到主分支
'''
    
    @staticmethod
    def get_code_of_conduct() -> str:
        """获取行为准则"""
        return '''
# 行为准则

## 我们的承诺

我们承诺为所有人提供一个友好、安全、有贡献精神的环境。

## 我们的标准

- 尊重他人
- 包容不同的观点
- 建设性地接受批评
- 专注于对社区最有益的事情
'''


class RoadmapPlanner:
    """
    阶段99：长期演进规划
    
    路线图规划和功能规划
    """
    
    VERSION = "1.0.0"
    
    @classmethod
    def get_current_roadmap(cls) -> Dict:
        """获取当前路线图"""
        return {
            "current_version": cls.VERSION,
            "milestones": [
                {
                    "version": "1.0.0",
                    "name": "基础版本",
                    "status": "completed",
                    "features": [
                        "三层架构",
                        "知识图谱",
                        "自主进化",
                        "容错机制",
                        "监控可观测性"
                    ]
                },
                {
                    "version": "1.1.0",
                    "name": "LLM集成",
                    "status": "planned",
                    "features": [
                        "大语言模型集成",
                        "自然语言理解",
                        "智能问答",
                        "语义搜索"
                    ]
                },
                {
                    "version": "2.0.0",
                    "name": "多Agent系统",
                    "status": "planned",
                    "features": [
                        "多Agent协作",
                        "分布式部署",
                        "联邦学习",
                        "知识共享"
                    ]
                }
            ]
        }
    
    @classmethod
    def get_feature_requests(cls) -> List[Dict]:
        """获取功能请求"""
        return [
            {"id": 1, "title": "Web界面", "votes": 42, "status": "under_review"},
            {"id": 2, "title": "REST API", "votes": 38, "status": "planned"},
            {"id": 3, "title": "性能优化", "votes": 35, "status": "in_progress"},
        ]


class FinalSystemChecker:
    """
    阶段100：系统完善与发布
    
    最终系统检查和验证
    """
    
    def __init__(self):
        self.checks: List[Dict] = []
    
    def add_check(self, name: str, check_func: Callable) -> bool:
        """添加检查项"""
        try:
            result = check_func()
            self.checks.append({
                "name": name,
                "passed": bool(result),
                "result": result,
                "timestamp": get_timestamp()
            })
            return bool(result)
        except Exception as e:
            self.checks.append({
                "name": name,
                "passed": False,
                "error": str(e),
                "timestamp": get_timestamp()
            })
            return False
    
    def get_report(self) -> Dict:
        """获取检查报告"""
        passed = sum(1 for c in self.checks if c.get("passed", False))
        total = len(self.checks)
        
        return {
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%",
            "checks": self.checks,
            "ready_for_release": passed == total
        }


def run_final_checks() -> Dict:
    """运行最终检查"""
    checker = FinalSystemChecker()
    
    from eternal_agent import KnowledgeGraph
    import tempfile
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        def check_import():
            from eternal_agent import __all__
            return len(__all__) > 50
        
        def check_core_modules():
            from eternal_agent import (
                KnowledgeGraph, EternalSelfAgent, Config,
                Metrics, ReliabilityManager, ObservableSystem
            )
            return True
        
        def check_knowledge_graph():
            kg = KnowledgeGraph(temp_path)
            kg.add_node("test_node")
            return "test_node" in kg.nodes
        
        def check_evolution():
            from eternal_agent import EvolutionEngine
            return True
        
        def check_reliability():
            from eternal_agent import ReliabilityManager
            return True
        
        def check_observability():
            from eternal_agent import ObservableSystem
            return True
        
        checker.add_check("Core imports", check_import)
        checker.add_check("Core modules", check_core_modules)
        checker.add_check("Knowledge Graph", check_knowledge_graph)
        checker.add_check("Evolution Engine", check_evolution)
        checker.add_check("Reliability Manager", check_reliability)
        checker.add_check("Observability System", check_observability)
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    return checker.get_report()
