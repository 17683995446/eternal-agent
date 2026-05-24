"""
阶段51-60：功能增强与扩展
- 节点属性扩展
- 边权重动态调整
- 知识图谱遍历算法
- 关联度计算增强
- 节点分类与标签
- 知识回溯功能
- 批量操作优化
- LRU缓存机制
"""
from typing import Dict, List, Any, Optional, Set, Callable, Deque
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import time

from .utils import logger


# ==========================================
# 阶段51：节点属性扩展
# ==========================================

class AttributeIndex:
    """节点属性索引 - 优化属性查询"""
    def __init__(self):
        self._attribute_map: Dict[str, Dict[Any, Set[str]]] = defaultdict(lambda: defaultdict(set))
    
    def index_node(self, node_name: str, attributes: Dict[str, Any]):
        """为节点属性建立索引"""
        for key, value in attributes.items():
            self._attribute_map[key][value].add(node_name)
    
    def find_by_attribute(self, key: str, value: Any) -> Set[str]:
        """根据属性值查找节点"""
        return self._attribute_map.get(key, {}).get(value, set())
    
    def remove_node(self, node_name: str, attributes: Dict[str, Any]):
        """从索引中移除节点"""
        for key, value in attributes.items():
            if key in self._attribute_map and value in self._attribute_map[key]:
                self._attribute_map[key][value].discard(node_name)
                if not self._attribute_map[key][value]:
                    del self._attribute_map[key][value]


# ==========================================
# 阶段52：边权重动态调整
# ==========================================

class WeightManager:
    """权重管理器 - 动态调整边权重"""
    
    def __init__(
        self,
        decay_rate: float = 0.99,
        boost_factor: float = 1.2,
        min_weight: float = 0.01,
        max_weight: float = 1.0
    ):
        self.decay_rate = decay_rate
        self.boost_factor = boost_factor
        self.min_weight = min_weight
        self.max_weight = max_weight
    
    def decay(self, weight: float) -> float:
        """权重衰减 - 阶段52"""
        new_weight = weight * self.decay_rate
        return max(new_weight, self.min_weight)
    
    def boost(self, weight: float) -> float:
        """权重强化 - 阶段52"""
        new_weight = weight * self.boost_factor
        return min(new_weight, self.max_weight)
    
    def normalize(self, weights: List[float]) -> List[float]:
        """权重归一化 - 阶段52"""
        if not weights:
            return []
        total = sum(weights)
        if total == 0:
            return weights
        return [w / total for w in weights]
    
    def adjust_based_on_usage(
        self,
        weight: float,
        used: bool,
        use_count: int = 0
    ) -> float:
        """根据使用情况调整权重"""
        if used:
            # 使用过则强化
            boost_amount = 1.0 + (use_count * 0.05)
            return min(weight * boost_amount, self.max_weight)
        else:
            # 未使用则衰减
            return self.decay(weight)


# ==========================================
# 阶段53：多类型任务支持
# ==========================================

class TaskType(Enum):
    """任务类型枚举 - 阶段53"""
    KNOWLEDGE_EVOLUTION = "knowledge_evolution"
    KNOWLEDGE_PRUNING = "knowledge_pruning"
    KNOWLEDGE_DISCOVERY = "knowledge_discovery"
    SYSTEM_MAINTENANCE = "system_maintenance"
    INITIALIZATION = "initialization"


@dataclass
class TypedTask:
    """带类型的任务 - 阶段53"""
    name: str
    task_type: TaskType
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==========================================
# 阶段54：任务优先级机制 + 优先级队列
# ==========================================

class PriorityQueue:
    """优先级任务队列 - 阶段54"""
    
    def __init__(self, max_size: int = 200):
        self.max_size = max_size
        self._tasks: List[TypedTask] = []
    
    def add(self, task: TypedTask) -> bool:
        """添加任务，按优先级排序"""
        if len(self._tasks) >= self.max_size:
            # 队列满，移除最低优先级任务
            self._tasks.sort(key=lambda t: t.priority)
            if task.priority > self._tasks[0].priority:
                self._tasks.pop(0)
            else:
                return False
        
        self._tasks.append(task)
        self._tasks.sort(key=lambda t: -t.priority)  # 高优先级在前
        return True
    
    def pop(self) -> Optional[TypedTask]:
        """获取最高优先级任务"""
        if not self._tasks:
            return None
        return self._tasks.pop(0)
    
    def is_empty(self) -> bool:
        return len(self._tasks) == 0
    
    def size(self) -> int:
        return len(self._tasks)
    
    def clear(self):
        self._tasks.clear()


# ==========================================
# 阶段55：知识图谱遍历算法
# ==========================================

class GraphTraverser:
    """图谱遍历器 - 阶段55"""
    
    def __init__(self, get_edges_from: Callable[[str], List]):
        self.get_edges_from = get_edges_from
    
    def dfs(self, start_node: str, max_depth: int = 10) -> List[str]:
        """深度优先遍历 - 阶段55"""
        visited: Set[str] = set()
        path: List[str] = []
        stack: Deque = deque([(start_node, 0)])
        
        while stack:
            node, depth = stack.pop()
            
            if node in visited or depth > max_depth:
                continue
            
            visited.add(node)
            path.append(node)
            
            # 获取边并倒序入栈以保持顺序
            edges = self.get_edges_from(node)
            for edge in reversed(edges):
                if edge.target not in visited:
                    stack.append((edge.target, depth + 1))
        
        return path
    
    def bfs(self, start_node: str, max_depth: int = 10) -> List[str]:
        """广度优先遍历 - 阶段55"""
        visited: Set[str] = set()
        path: List[str] = []
        queue: Deque = deque([(start_node, 0)])
        
        while queue:
            node, depth = queue.popleft()
            
            if node in visited or depth > max_depth:
                continue
            
            visited.add(node)
            path.append(node)
            
            edges = self.get_edges_from(node)
            for edge in edges:
                if edge.target not in visited:
                    queue.append((edge.target, depth + 1))
        
        return path
    
    def find_path(self, start: str, end: str, max_depth: int = 10) -> Optional[List[str]]:
        """查找两点之间的路径 - 阶段55"""
        if start == end:
            return [start]
        
        visited: Set[str] = set()
        parent: Dict[str, str] = {}
        queue: Deque = deque([(start, 0)])
        visited.add(start)
        
        while queue:
            node, depth = queue.popleft()
            
            if depth > max_depth:
                continue
            
            edges = self.get_edges_from(node)
            for edge in edges:
                if edge.target == end:
                    # 找到终点，重建路径
                    path = [end, node]
                    current = node
                    while current in parent:
                        current = parent[current]
                        path.append(current)
                    return list(reversed(path))
                
                if edge.target not in visited:
                    visited.add(edge.target)
                    parent[edge.target] = node
                    queue.append((edge.target, depth + 1))
        
        return None


# ==========================================
# 阶段56：关联度计算增强
# ==========================================

class RelevanceCalculator:
    """关联度计算器 - 阶段56"""
    
    def __init__(self, get_edges_from: Callable[[str], List]):
        self.get_edges_from = get_edges_from
    
    def multi_hop_relevance(
        self,
        node: str,
        max_hops: int = 3,
        decay: float = 0.7
    ) -> Dict[str, float]:
        """多跳关联度计算 - 阶段56"""
        relevance: Dict[str, float] = {node: 1.0}
        current_nodes: Dict[str, float] = {node: 1.0}
        
        for hop in range(max_hops):
            next_nodes: Dict[str, float] = {}
            
            for n, score in current_nodes.items():
                edges = self.get_edges_from(n)
                for edge in edges:
                    new_score = score * edge.weight * decay
                    if edge.target in relevance:
                        relevance[edge.target] = max(relevance[edge.target], new_score)
                    else:
                        relevance[edge.target] = new_score
                    
                    if edge.target in next_nodes:
                        next_nodes[edge.target] = max(next_nodes[edge.target], new_score)
                    else:
                        next_nodes[edge.target] = new_score
            
            current_nodes = next_nodes
        
        return relevance
    
    def get_recommendations(
        self,
        node: str,
        top_k: int = 5,
        max_hops: int = 2
    ) -> List[tuple]:
        """获取关联推荐 - 阶段56"""
        relevance = self.multi_hop_relevance(node, max_hops)
        # 排除自身
        if node in relevance:
            del relevance[node]
        
        sorted_nodes = sorted(
            relevance.items(),
            key=lambda x: -x[1]
        )
        return sorted_nodes[:top_k]


# ==========================================
# 阶段57：节点分类与标签
# ==========================================

class TagManager:
    """标签管理器 - 阶段57"""
    
    def __init__(self):
        self._node_tags: Dict[str, Set[str]] = defaultdict(set)
        self._tag_nodes: Dict[str, Set[str]] = defaultdict(set)
    
    def add_tag(self, node_name: str, tag: str):
        """为节点添加标签 - 阶段57"""
        self._node_tags[node_name].add(tag)
        self._tag_nodes[tag].add(node_name)
    
    def remove_tag(self, node_name: str, tag: str):
        """移除节点标签"""
        if tag in self._node_tags[node_name]:
            self._node_tags[node_name].remove(tag)
        if node_name in self._tag_nodes[tag]:
            self._tag_nodes[tag].remove(node_name)
    
    def get_tags(self, node_name: str) -> Set[str]:
        """获取节点的所有标签"""
        return set(self._node_tags.get(node_name, set()))
    
    def get_nodes_by_tag(self, tag: str) -> Set[str]:
        """根据标签查询节点 - 阶段57"""
        return set(self._tag_nodes.get(tag, set()))
    
    def get_all_tags(self) -> Set[str]:
        """获取所有使用的标签"""
        return set(self._tag_nodes.keys())
    
    def get_tag_statistics(self) -> Dict[str, int]:
        """获取标签统计 - 阶段57"""
        return {tag: len(nodes) for tag, nodes in self._tag_nodes.items()}


# ==========================================
# 阶段58：知识回溯功能
# ==========================================

@dataclass
class HistoryRecord:
    """历史记录 - 阶段58"""
    action: str
    node_name: Optional[str] = None
    edge_info: Optional[Dict] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HistoryTracker:
    """知识回溯追踪器 - 阶段58"""
    
    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self._records: Deque[HistoryRecord] = deque(maxlen=max_records)
        self._node_history: Dict[str, List[HistoryRecord]] = defaultdict(list)
    
    def record_add_node(self, node_name: str, **metadata):
        """记录节点添加 - 阶段58"""
        record = HistoryRecord(
            action="add_node",
            node_name=node_name,
            metadata=metadata
        )
        self._records.append(record)
        self._node_history[node_name].append(record)
    
    def record_add_edge(self, source: str, target: str, relation: str, weight: float, **metadata):
        """记录边添加 - 阶段58"""
        record = HistoryRecord(
            action="add_edge",
            edge_info={
                "source": source,
                "target": target,
                "relation": relation,
                "weight": weight
            },
            metadata=metadata
        )
        self._records.append(record)
        self._node_history[source].append(record)
        self._node_history[target].append(record)
    
    def record_prune_edge(self, source: str, target: str, **metadata):
        """记录边修剪"""
        record = HistoryRecord(
            action="prune_edge",
            edge_info={"source": source, "target": target},
            metadata=metadata
        )
        self._records.append(record)
    
    def record_remove_node(self, node_name: str, **metadata):
        """记录节点删除"""
        record = HistoryRecord(
            action="remove_node",
            node_name=node_name,
            metadata=metadata
        )
        self._records.append(record)
    
    def record_remove_edge(self, source: str, target: str, **metadata):
        """记录边删除"""
        record = HistoryRecord(
            action="remove_edge",
            edge_info={"source": source, "target": target},
            metadata=metadata
        )
        self._records.append(record)
    
    def get_node_history(self, node_name: str, limit: int = 50) -> List[HistoryRecord]:
        """获取节点历史 - 阶段58"""
        return list(self._node_history.get(node_name, []))[-limit:]
    
    def get_recent_records(self, limit: int = 100) -> List[HistoryRecord]:
        """获取最近记录"""
        return list(self._records)[-limit:]
    
    def get_knowledge_origin(self, node_name: str) -> Optional[List[HistoryRecord]]:
        """获取知识溯源路径 - 阶段58"""
        # 简化版本：返回节点的创建历史
        return self._node_history.get(node_name, [])


# ==========================================
# 阶段60：LRU缓存机制
# ==========================================

class LRUCache:
    """LRU缓存 - 阶段60"""
    
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self._cache: Dict[str, Any] = {}
        self._access_order: Deque[str] = deque()
        self._access_count: Dict[str, int] = defaultdict(int)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值 - 阶段60"""
        if key not in self._cache:
            return None
        
        # 更新访问顺序：先移除再添加到末尾
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        self._access_count[key] += 1
        
        return self._cache[key]
    
    def put(self, key: str, value: Any):
        """设置缓存值 - 阶段60"""
        # 如果key已存在，更新值和访问顺序
        if key in self._cache:
            self._cache[key] = value
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            self._access_count[key] += 1
            return
        
        # 如果满了，移除最久未使用的（队首）
        if len(self._cache) >= self.capacity:
            lru_key = self._access_order.popleft()
            del self._cache[lru_key]
            if lru_key in self._access_count:
                del self._access_count[lru_key]
        
        # 添加新值
        self._cache[key] = value
        self._access_order.append(key)
        self._access_count[key] = 1
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
        self._access_count.clear()
    
    def size(self) -> int:
        return len(self._cache)
    
    def get_hit_rate(self) -> float:
        """获取缓存命中率（估算）"""
        total_access = sum(self._access_count.values())
        if total_access == 0:
            return 0.0
        # 简化计算
        return min(1.0, len(self._access_count) / max(len(self._cache), 1))
