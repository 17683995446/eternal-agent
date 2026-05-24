"""
阶段46：监控指标收集
"""
import time
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class Metrics:
    """运行时指标"""
    start_time: float = field(default_factory=time.time)
    total_tasks_executed: int = 0
    total_nodes_added: int = 0
    total_edges_added: int = 0
    total_trim_operations: int = 0
    total_exceptions: int = 0
    last_update_time: float = field(default_factory=time.time)
    
    def update_task_count(self):
        """更新任务计数"""
        self.total_tasks_executed += 1
        self.last_update_time = time.time()
    
    def update_node_count(self):
        """更新节点计数"""
        self.total_nodes_added += 1
        self.last_update_time = time.time()
    
    def update_edge_count(self):
        """更新边计数"""
        self.total_edges_added += 1
        self.last_update_time = time.time()
    
    def update_trim_count(self):
        """更新修剪计数"""
        self.total_trim_operations += 1
        self.last_update_time = time.time()
    
    def update_exception_count(self):
        """更新异常计数"""
        self.total_exceptions += 1
        self.last_update_time = time.time()
    
    def get_stats(self, kg_stats: Dict[str, int] = None) -> Dict[str, Any]:
        """获取完整统计信息"""
        uptime = time.time() - self.start_time
        stats = {
            "uptime_seconds": round(uptime, 2),
            "total_tasks_executed": self.total_tasks_executed,
            "total_nodes_added": self.total_nodes_added,
            "total_edges_added": self.total_edges_added,
            "total_trim_operations": self.total_trim_operations,
            "total_exceptions": self.total_exceptions,
            "tasks_per_second": round(self.total_tasks_executed / max(uptime, 1), 2)
        }
        if kg_stats:
            stats.update(kg_stats)
        return stats


# 全局指标实例
global_metrics = Metrics()
