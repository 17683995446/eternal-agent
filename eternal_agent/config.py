"""
阶段45：配置管理
"""
import json
import os
from typing import Any, Dict


DEFAULT_CONFIG = {
    "loop_delay": 0.3,
    "evolve_step": 50,
    "kg_save_path": "knowledge_graph.json",
    "task_queue_max": 200,
    "min_weight_for_derive": 0.2,
    "min_weight_for_keep": 0.1,
    "default_edge_weight": 0.8,
    "log_level": "INFO",
    "enable_auto_trim": True
}


class Config:
    """配置管理器"""
    
    def __init__(self, config_path: str = "agent_config.json"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception:
                self._config = DEFAULT_CONFIG.copy()
                self.save()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self._config[key] = value
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return dict(self._config)


# 全局配置实例
global_config = Config()
