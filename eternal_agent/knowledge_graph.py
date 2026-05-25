"""
阶段6-20 + 阶段43 + 阶段51-60：知识记忆层实现
- 阶段51：节点属性扩展
- 阶段52：边权重动态调整
- 阶段55-57：遍历、关联度、标签
- 阶段58：知识回溯
- 阶段59：批量操作优化
- 阶段60：LRU缓存
"""
from typing import Dict, List, Any, Optional, Tuple
import os
from collections import defaultdict
from dataclasses import dataclass, asdict

from .constants import (
    KG_SAVE_PATH,
    MIN_WEIGHT_FOR_DERIVE,
    MIN_WEIGHT_FOR_KEEP,
    DEFAULT_EDGE_WEIGHT
)
from .utils import save_json, load_json, get_timestamp, logger
from .config import global_config
from .metrics import global_metrics
from .advanced import (
    AttributeIndex,
    WeightManager,
    GraphTraverser,
    RelevanceCalculator,
    TagManager,
    HistoryTracker,
    LRUCache
)


@dataclass
class Node:
    """阶段7 + 阶段51：节点数据结构 + 属性扩展"""
    name: str
    created_at: float
    is_valid: bool = True
    attributes: Dict[str, Any] = None
    # 阶段57：标签列表
    tags: List[str] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.tags is None:
            self.tags = []


@dataclass
class Edge:
    """阶段8 + 阶段52：边数据结构 + 使用计数"""
    source: str
    target: str
    relation_name: str
    weight: float
    created_at: float
    # 阶段52：使用计数，用于权重调整
    use_count: int = 0


class KnowledgeGraph:
    """
    记忆层核心类：知识图谱
    阶段51-60增强版本
    """

    def __init__(self, save_path: str = None):
        logger.info("[System] Initializing KnowledgeGraph")
        if save_path is None:
            save_path = global_config.get("kg_save_path", KG_SAVE_PATH)
        self.save_path = save_path
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        # 阶段43优化：边索引
        self._source_index: Dict[str, List[Edge]] = defaultdict(list)
        self._pending_changes = 0
        self._save_threshold = 10  # 累积10个变更再保存
        
        # 阶段51：属性索引
        logger.info("[System] Initializing AttributeIndex")
        self._attribute_index = AttributeIndex()
        # 阶段52：权重管理器
        logger.info("[System] Initializing WeightManager")
        self._weight_manager = WeightManager()
        # 阶段55：图谱遍历器
        logger.info("[System] Initializing GraphTraverser")
        self._traverser = GraphTraverser(self.get_edges_from)
        # 阶段56：关联度计算器
        logger.info("[System] Initializing RelevanceCalculator")
        self._relevance = RelevanceCalculator(self.get_edges_from)
        # 阶段57：标签管理器
        logger.info("[System] Initializing TagManager")
        self._tag_manager = TagManager()
        # 阶段58：历史追踪器
        logger.info("[System] Initializing HistoryTracker")
        self._history = HistoryTracker()
        # 阶段60：LRU缓存
        logger.info("[System] Initializing LRUCache")
        self._node_cache = LRUCache(capacity=200)
        self._edge_cache = LRUCache(capacity=300)
        
        logger.info("[System] Loading knowledge from disk")
        self.load()
        logger.info("[System] KnowledgeGraph initialization complete")

    def load(self) -> None:
        """
        阶段11：记忆加载
        满足记忆公理 - 重启不丢失经验
        """
        logger.info("[KnowledgeGraph] Loading from %s", self.save_path)
        if os.path.exists(self.save_path):
            try:
                data = load_json(self.save_path)
                if data:
                    # 加载节点
                    logger.info("[KnowledgeGraph] Loading %d nodes from data", len(data.get('nodes', [])))
                    for node_data in data.get('nodes', []):
                        node = Node(**node_data)
                        self.nodes[node.name] = node
                        if node.attributes:
                            self._attribute_index.index_node(node.name, node.attributes)
                    # 加载边并重建索引
                    logger.info("[KnowledgeGraph] Loading %d edges from data", len(data.get('edges', [])))
                    for edge_data in data.get('edges', []):
                        edge = Edge(**edge_data)
                        self.edges.append(edge)
                        self._source_index[edge.source].append(edge)
                    logger.info("[KnowledgeGraph] Loaded %d nodes, %d edges", len(self.nodes), len(self.edges))
                    return
            except Exception as e:
                logger.warning("[KnowledgeGraph] Failed to load existing file, creating new: %s", e)
        
        # 如果文件不存在或加载失败，创建新的
        logger.info("[KnowledgeGraph] Creating new knowledge graph")
        self._save_immediate()

    def _save_immediate(self) -> None:
        """立即保存（不使用批量）"""
        logger.debug("[KnowledgeGraph] Saving to disk immediately")
        data = {
            'nodes': [asdict(node) for node in self.nodes.values()],
            'edges': [asdict(edge) for edge in self.edges]
        }
        save_json(data, self.save_path)

    def save(self) -> None:
        """
        阶段12+43：记忆固化 + 批量优化
        满足记忆公理 - 所有行为永久结构化留存
        """
        self._pending_changes += 1
        logger.debug("[KnowledgeGraph] Pending changes: %d / %d", self._pending_changes, self._save_threshold)
        if self._pending_changes >= self._save_threshold:
            self._save_immediate()
            self._pending_changes = 0

    def force_save(self) -> None:
        """强制立即保存"""
        logger.info("[KnowledgeGraph] Force save")
        self._save_immediate()
        self._pending_changes = 0

    # ==========================================
    # 增强版：支持历史记录和索引 - 阶段51+58
    # ==========================================
    
    def add_node(self, name: str, attributes: Dict[str, Any] = None) -> None:
        """
        新增认知实体 - 阶段13
        增强版：支持历史记录和属性索引
        """
        logger.debug("[KnowledgeGraph] add_node called: %s", name)
        if not isinstance(name, str) or not name:
            logger.warning("[KnowledgeGraph] Invalid node name: %s", name)
            return
            
        if name not in self.nodes:
            node = Node(
                name=name,
                created_at=get_timestamp(),
                is_valid=True,
                attributes=attributes
            )
            self.nodes[name] = node
            if attributes:
                self._attribute_index.index_node(name, attributes)
            self._history.record_add_node(name)
            global_metrics.update_node_count()
            self.save()
            logger.debug("[KnowledgeGraph] Added node: %s", name)

    def add_edge(
        self,
        source: str,
        target: str,
        relation_name: str,
        weight: float = None
    ) -> None:
        """
        新增加权关系（智能迭代核心）- 阶段14
        增强版：支持历史记录
        """
        logger.debug("[KnowledgeGraph] add_edge called: %s -> %s (%s)", source, target, relation_name)
        if weight is None:
            weight = global_config.get("default_edge_weight", DEFAULT_EDGE_WEIGHT)
        
        # 自动保证头尾节点存在
        self.add_node(source)
        self.add_node(target)
        
        edge = Edge(
            source=source,
            target=target,
            relation_name=relation_name,
            weight=weight,
            created_at=get_timestamp()
        )
        self.edges.append(edge)
        self._source_index[source].append(edge)
        self._history.record_add_edge(source, target, relation_name, weight)
        global_metrics.update_edge_count()
        self.save()
        logger.debug("[KnowledgeGraph] Added edge: %s -> %s (%s, %f)", source, target, relation_name, weight)

    def derive_new_tasks(self, node_name: str) -> List[str]:
        """
        阶段31+43：自驱核心 + 索引优化
        基于已有知识推演新生任务（永动来源）
        """
        logger.debug("[KnowledgeGraph] derive_new_tasks for node: %s", node_name)
        min_weight = global_config.get("min_weight_for_derive", MIN_WEIGHT_FOR_DERIVE)
        new_tasks = []
        seen = set()
        
        # 阶段43优化：使用索引而不是遍历所有边
        for edge in self._source_index.get(node_name, []):
            if edge.weight > min_weight:
                task = f"知识推演任务:{edge.target}"
                if task not in seen:
                    new_tasks.append(task)
                    seen.add(task)
        
        logger.debug("[KnowledgeGraph] Derived %d tasks", len(new_tasks))
        return new_tasks

    def trim_invalid_knowledge(self) -> None:
        """
        阶段32：进化能力 - 自驱公理：自动淘汰低价值知识，防臃肿老化
        """
        if not global_config.get("enable_auto_trim", True):
            logger.debug("[KnowledgeGraph] Auto trim disabled")
            return
            
        logger.info("[KnowledgeGraph] Starting trim operation")
        min_weight = global_config.get("min_weight_for_keep", MIN_WEIGHT_FOR_KEEP)
        original_count = len(self.edges)
        self.edges = [edge for edge in self.edges if edge.weight > min_weight]
        trimmed = original_count - len(self.edges)
        
        if trimmed > 0:
            # 重建索引
            self._source_index.clear()
            for edge in self.edges:
                self._source_index[edge.source].append(edge)
            global_metrics.update_trim_count()
            self.force_save()
            logger.info("[KnowledgeGraph] Trimmed %d low-weight edges", trimmed)

    def get_node(self, name: str) -> Optional[Node]:
        """阶段16：按名称查找节点"""
        return self.nodes.get(name)

    def get_edges_from(self, source: str) -> List[Edge]:
        """阶段17+43：按源节点查询边 - 使用索引优化"""
        return list(self._source_index.get(source, []))

    def get_edges_to(self, target: str) -> List[Edge]:
        """阶段17：按目标节点查询边"""
        return [edge for edge in self.edges if edge.target == target]

    def get_stats(self) -> Dict[str, int]:
        """获取知识图谱统计信息"""
        return {
            'nodes_count': len(self.nodes),
            'edges_count': len(self.edges)
        }
    
    # ==========================================
    # 阶段51：节点属性扩展
    # ==========================================
    
    def update_node_attribute(
        self,
        node_name: str,
        key: str,
        value: Any
    ):
        """更新节点属性 - 阶段51"""
        logger.debug("[KnowledgeGraph] update_node_attribute: %s.%s = %s", node_name, key, value)
        if node_name not in self.nodes:
            return
        
        node = self.nodes[node_name]
        # 从索引中移除旧值
        if key in node.attributes:
            old_value = node.attributes[key]
            self._attribute_index.remove_node(node_name, {key: old_value})
        
        # 设置新值
        node.attributes[key] = value
        # 索引新值
        self._attribute_index.index_node(node_name, {key: value})
        self.save()
    
    def find_nodes_by_attribute(
        self,
        key: str,
        value: Any
    ) -> List[str]:
        """根据属性查找节点 - 阶段51"""
        logger.debug("[KnowledgeGraph] find_nodes_by_attribute: %s=%s", key, value)
        result = list(self._attribute_index.find_by_attribute(key, value))
        logger.debug("[KnowledgeGraph] Found %d nodes", len(result))
        return result
    
    # ==========================================
    # 阶段52：边权重动态调整
    # ==========================================
    
    def record_edge_usage(
        self,
        source: str,
        target: str
    ):
        """记录边的使用 - 阶段52"""
        logger.debug("[KnowledgeGraph] record_edge_usage: %s -> %s", source, target)
        for edge in self._source_index.get(source, []):
            if edge.target == target:
                edge.use_count += 1
                # 强化权重
                edge.weight = self._weight_manager.boost(edge.weight)
                logger.debug("[KnowledgeGraph] Edge usage incremented: count=%d, weight=%f", edge.use_count, edge.weight)
                break
    
    def decay_all_weights(self):
        """衰减所有边权重 - 阶段52"""
        logger.info("[KnowledgeGraph] Decaying all edge weights")
        for edge in self.edges:
            edge.weight = self._weight_manager.decay(edge.weight)
        self.force_save()
    
    # ==========================================
    # 阶段55：知识图谱遍历算法
    # ==========================================
    
    def dfs_traversal(
        self,
        start_node: str,
        max_depth: int = 10
    ) -> List[str]:
        """深度优先遍历 - 阶段55"""
        logger.debug("[KnowledgeGraph] DFS starting from: %s", start_node)
        result = self._traverser.dfs(start_node, max_depth)
        logger.debug("[KnowledgeGraph] DFS visited %d nodes", len(result))
        return result
    
    def bfs_traversal(
        self,
        start_node: str,
        max_depth: int = 10
    ) -> List[str]:
        """广度优先遍历 - 阶段55"""
        logger.debug("[KnowledgeGraph] BFS starting from: %s", start_node)
        result = self._traverser.bfs(start_node, max_depth)
        logger.debug("[KnowledgeGraph] BFS visited %d nodes", len(result))
        return result
    
    def find_path(
        self,
        start: str,
        end: str,
        max_depth: int = 10
    ) -> Optional[List[str]]:
        """查找两点之间的路径 - 阶段55"""
        logger.debug("[KnowledgeGraph] Finding path: %s -> %s", start, end)
        result = self._traverser.find_path(start, end, max_depth)
        logger.debug("[KnowledgeGraph] Path found: %s", result is not None)
        return result
    
    # ==========================================
    # 阶段56：关联度计算增强
    # ==========================================
    
    def get_multi_hop_relevance(
        self,
        node: str,
        max_hops: int = 3
    ) -> Dict[str, float]:
        """多跳关联度计算 - 阶段56"""
        logger.debug("[KnowledgeGraph] Multi-hop relevance for: %s (hops=%d)", node, max_hops)
        result = self._relevance.multi_hop_relevance(node, max_hops)
        logger.debug("[KnowledgeGraph] Relevance calculation complete: %d nodes", len(result))
        return result
    
    def get_recommendations(
        self,
        node: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """关联推荐 - 阶段56"""
        logger.debug("[KnowledgeGraph] Getting recommendations for: %s (top=%d)", node, top_k)
        result = self._relevance.get_recommendations(node, top_k)
        logger.debug("[KnowledgeGraph] Recommendation complete: %d items", len(result))
        return result
    
    # ==========================================
    # 阶段57：节点分类与标签
    # ==========================================
    
    def add_tag(self, node_name: str, tag: str):
        """为节点添加标签 - 阶段57"""
        logger.debug("[KnowledgeGraph] Adding tag: %s -> %s", node_name, tag)
        if node_name not in self.nodes:
            return
        self._tag_manager.add_tag(node_name, tag)
        if tag not in self.nodes[node_name].tags:
            self.nodes[node_name].tags.append(tag)
    
    def get_tags(self, node_name: str) -> List[str]:
        """获取节点标签 - 阶段57"""
        return list(self._tag_manager.get_tags(node_name))
    
    def get_nodes_by_tag(self, tag: str) -> List[str]:
        """根据标签查找节点 - 阶段57"""
        logger.debug("[KnowledgeGraph] Finding nodes by tag: %s", tag)
        return list(self._tag_manager.get_nodes_by_tag(tag))
    
    def get_tag_statistics(self) -> Dict[str, int]:
        """获取标签统计 - 阶段57"""
        return self._tag_manager.get_tag_statistics()
    
    # ==========================================
    # 阶段58：知识回溯功能
    # ==========================================
    
    def get_node_history(
        self,
        node_name: str,
        limit: int = 50
    ):
        """获取节点历史 - 阶段58"""
        logger.debug("[KnowledgeGraph] Getting history for node: %s", node_name)
        return self._history.get_node_history(node_name, limit)
    
    def get_recent_history(self, limit: int = 100):
        """获取最近历史 - 阶段58"""
        return self._history.get_recent_records(limit)
    
    # ==========================================
    # 阶段59：批量操作优化
    # ==========================================
    
    def batch_add_nodes(
        self,
        node_data_list: List[Tuple[str, Dict[str, Any]]]
    ) -> int:
        """批量添加节点 - 阶段59"""
        logger.info("[KnowledgeGraph] Starting batch add of %d nodes", len(node_data_list))
        count = 0
        for name, attributes in node_data_list:
            if name not in self.nodes:
                node = Node(
                    name=name,
                    created_at=get_timestamp(),
                    attributes=attributes
                )
                self.nodes[name] = node
                self._attribute_index.index_node(name, attributes)
                self._history.record_add_node(name)
                global_metrics.update_node_count()
                count += 1
        
        if count > 0:
            self.force_save()
        
        logger.info("[KnowledgeGraph] Batch add complete: %d nodes added", count)
        return count
    
    def batch_add_edges(
        self,
        edge_data_list: List[Tuple[str, str, str, float]]
    ) -> int:
        """批量添加边 - 阶段59"""
        logger.info("[KnowledgeGraph] Starting batch add of %d edges", len(edge_data_list))
        count = 0
        for source, target, relation, weight in edge_data_list:
            # 确保源和目标节点存在
            self.add_node(source)
            self.add_node(target)
            
            edge = Edge(
                source=source,
                target=target,
                relation_name=relation,
                weight=weight,
                created_at=get_timestamp()
            )
            self.edges.append(edge)
            self._source_index[source].append(edge)
            self._history.record_add_edge(source, target, relation, weight)
            global_metrics.update_edge_count()
            count += 1
        
        if count > 0:
            self.force_save()
        
        logger.info("[KnowledgeGraph] Batch add complete: %d edges added", count)
        return count
    
    # ==========================================
    # 阶段61-70需要的辅助方法
    # ==========================================
    
    def has_edge(self, source: str, target: str) -> bool:
        """检查边是否存在"""
        for edge in self._source_index.get(source, []):
            if edge.target == target:
                return True
        return False
    
    def get_edge(self, source: str, target: str) -> Optional[Edge]:
        """获取边"""
        for edge in self._source_index.get(source, []):
            if edge.target == target:
                return edge
        return None
    
    def update_edge_weight(self, source: str, target: str, new_weight: float):
        """更新边权重"""
        logger.debug("[KnowledgeGraph] Updating edge weight: %s -> %s, new=%f", source, target, new_weight)
        edge = self.get_edge(source, target)
        if edge:
            edge.weight = max(0.0, min(1.0, new_weight))
            self.save()
    
    def remove_node(self, node_name: str):
        """移除节点"""
        logger.info("[KnowledgeGraph] Removing node: %s", node_name)
        if node_name not in self.nodes:
            logger.debug("[KnowledgeGraph] Node not found for removal")
            return
        
        # 移除相关边
        edges_to_remove = []
        for edge in self.edges:
            if edge.source == node_name or edge.target == node_name:
                edges_to_remove.append(edge)
        
        logger.debug("[KnowledgeGraph] Removing %d related edges", len(edges_to_remove))
        for edge in edges_to_remove:
            self.remove_edge(edge.source, edge.target)
        
        # 移除属性索引
        node = self.nodes[node_name]
        if node.attributes:
            self._attribute_index.remove_node(node_name, node.attributes)
        
        # 移除标签
        for tag in node.tags:
            self._tag_manager.remove_tag(node_name, tag)
        
        # 移除节点
        del self.nodes[node_name]
        self._history.record_remove_node(node_name)
        self.force_save()
        logger.info("[KnowledgeGraph] Node removed: %s", node_name)
    
    def remove_edge(self, source: str, target: str):
        """移除边"""
        logger.debug("[KnowledgeGraph] Removing edge: %s -> %s", source, target)
        edge = self.get_edge(source, target)
        if edge:
            self.edges.remove(edge)
            # 更新索引
            self._source_index[source].remove(edge)
            self._history.record_remove_edge(source, target)
            self.save()
    
    def get_neighbors(self, node_name: str) -> List[str]:
        """获取节点的邻居"""
        neighbors = []
        for edge in self._source_index.get(node_name, []):
            neighbors.append(edge.target)
        return neighbors
