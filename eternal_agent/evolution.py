"""
基于第一性原理的轻量永动知识图谱 Agent
阶段61-70：高级进化能力
"""

import logging
import math
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime
import random
from .knowledge_graph import KnowledgeGraph, Node, Edge

logger = logging.getLogger("EternalAgent")

# ========================================
# 阶段61：知识聚类算法
# ========================================

class KnowledgeClusterer:
    """知识聚类器 - 基于节点相似度和关系密度进行聚类"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.clusters: Dict[int, Set[str]] = {}  # 簇ID -> 节点名集合
        self.node_to_cluster: Dict[str, int] = {}  # 节点名 -> 簇ID
        self.next_cluster_id = 0
    
    def compute_node_similarity(self, node1: str, node2: str) -> float:
        """
        计算两个节点的相似度
        基于：共同邻居数量、标签重叠度、属性相似度
        """
        if node1 not in self.kg.nodes or node2 not in self.kg.nodes:
            return 0.0
        
        # 共同邻居
        neighbors1 = set(self.kg.get_neighbors(node1))
        neighbors2 = set(self.kg.get_neighbors(node2))
        common_neighbors = neighbors1 & neighbors2
        all_neighbors = neighbors1 | neighbors2
        neighbor_sim = len(common_neighbors) / len(all_neighbors) if all_neighbors else 0.0
        
        # 标签相似度
        tags1 = self.kg._tag_manager.get_tags(node1) if hasattr(self.kg, '_tag_manager') else set()
        tags2 = self.kg._tag_manager.get_tags(node2) if hasattr(self.kg, '_tag_manager') else set()
        common_tags = tags1 & tags2
        all_tags = tags1 | tags2
        tag_sim = len(common_tags) / len(all_tags) if all_tags else 0.0
        
        # 属性相似度
        attr1 = self.kg.nodes[node1].attributes or {}
        attr2 = self.kg.nodes[node2].attributes or {}
        common_attrs = set(attr1.keys()) & set(attr2.keys())
        attr_match = 0
        for key in common_attrs:
            if attr1.get(key) == attr2.get(key):
                attr_match += 1
        attr_sim = attr_match / len(common_attrs) if common_attrs else 0.0
        
        # 加权平均
        return 0.5 * neighbor_sim + 0.3 * tag_sim + 0.2 * attr_sim
    
    def cluster_nodes(self, similarity_threshold: float = 0.3) -> Dict[int, Set[str]]:
        """
        使用层次聚类算法对节点进行聚类
        """
        logger.info("Starting node clustering...")
        
        # 重置
        self.clusters = {}
        self.node_to_cluster = {}
        self.next_cluster_id = 0
        
        nodes = list(self.kg.nodes.keys())
        if not nodes:
            return self.clusters
        
        # 初始化每个节点为单独的簇
        for node in nodes:
            cluster_id = self.next_cluster_id
            self.clusters[cluster_id] = {node}
            self.node_to_cluster[node] = cluster_id
            self.next_cluster_id += 1
        
        # 层次聚类：迭代合并相似簇
        merged = True
        while merged:
            merged = False
            best_merge = None
            best_similarity = 0
            
            # 查找最相似的簇对
            cluster_ids = list(self.clusters.keys())
            for i in range(len(cluster_ids)):
                for j in range(i + 1, len(cluster_ids)):
                    c1, c2 = cluster_ids[i], cluster_ids[j]
                    sim = self._compute_cluster_similarity(c1, c2)
                    if sim > similarity_threshold and sim > best_similarity:
                        best_similarity = sim
                        best_merge = (c1, c2)
            
            # 合并最相似的簇
            if best_merge:
                c1, c2 = best_merge
                self.clusters[c1].update(self.clusters[c2])
                for node in self.clusters[c2]:
                    self.node_to_cluster[node] = c1
                del self.clusters[c2]
                merged = True
                logger.debug(f"Merged clusters {c1} and {c2}, similarity: {best_similarity:.2f}")
        
        logger.info(f"Clustering complete: {len(self.clusters)} clusters found")
        return self.clusters
    
    def _compute_cluster_similarity(self, cluster1: int, cluster2: int) -> float:
        """计算两个簇之间的平均相似度"""
        nodes1 = self.clusters.get(cluster1, set())
        nodes2 = self.clusters.get(cluster2, set())
        
        if not nodes1 or not nodes2:
            return 0.0
        
        total_sim = 0.0
        count = 0
        for n1 in nodes1:
            for n2 in nodes2:
                total_sim += self.compute_node_similarity(n1, n2)
                count += 1
        
        return total_sim / count if count > 0 else 0.0
    
    def get_cluster_of(self, node: str) -> Optional[Set[str]]:
        """获取节点所在的簇"""
        cluster_id = self.node_to_cluster.get(node)
        return self.clusters.get(cluster_id)
    
    def get_cluster_info(self) -> List[Dict]:
        """获取所有簇的详细信息"""
        info = []
        for cluster_id, nodes in self.clusters.items():
            info.append({
                "cluster_id": cluster_id,
                "size": len(nodes),
                "nodes": list(nodes),
                "center": self._find_cluster_center(cluster_id)
            })
        return sorted(info, key=lambda x: -x["size"])
    
    def _find_cluster_center(self, cluster_id: int) -> Optional[str]:
        """找到簇的中心节点（度最高的节点）"""
        nodes = self.clusters.get(cluster_id, set())
        if not nodes:
            return None
        return max(nodes, key=lambda n: len(self.kg.get_neighbors(n)))

# ========================================
# 阶段62：关联规则挖掘
# ========================================

class AssociationRuleMiner:
    """关联规则挖掘器 - 挖掘节点间的频繁模式"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def mine_frequent_patterns(self, min_support: float = 0.1) -> List[Tuple[Set[str], float]]:
        """
        挖掘频繁模式（基于Apriori算法简化版）
        """
        logger.info("Mining frequent patterns...")
        
        all_nodes = list(self.kg.nodes.keys())
        if not all_nodes:
            return []
        
        # 先计算单个节点的支持度
        node_support = {}
        total = len(all_nodes)
        
        for node in all_nodes:
            # 支持度：节点的邻居数量 / 总节点数
            support = len(self.kg.get_neighbors(node)) / max(total, 1)
            if support >= min_support:
                node_support[frozenset([node])] = support
        
        # 逐步组合
        patterns = list(node_support.items())
        k = 2
        
        while True:
            candidates = self._generate_candidates(patterns, k)
            if not candidates:
                break
            
            # 计算支持度
            new_patterns = []
            for candidate in candidates:
                support = self._compute_pattern_support(candidate)
                if support >= min_support:
                    new_patterns.append((candidate, support))
            
            if not new_patterns:
                break
            
            patterns.extend(new_patterns)
            k += 1
        
        logger.info(f"Found {len(patterns)} frequent patterns")
        return patterns
    
    def _generate_candidates(self, patterns: List[Tuple[Set[str], float]], k: int) -> List[Set[str]]:
        """生成k项候选集"""
        candidates = set()
        itemsets = [p[0] for p in patterns if len(p[0]) == k-1]
        
        for i in range(len(itemsets)):
            for j in range(i + 1, len(itemsets)):
                s1, s2 = itemsets[i], itemsets[j]
                union = s1 | s2
                if len(union) == k:
                    candidates.add(frozenset(union))
        
        return [set(c) for c in candidates]
    
    def _compute_pattern_support(self, pattern: Set[str]) -> float:
        """计算模式的支持度（基于连接密度）"""
        pattern_list = list(pattern)
        if len(pattern_list) < 2:
            return 0.0
        
        edges = 0
        possible_edges = len(pattern_list) * (len(pattern_list) - 1) / 2
        
        for i in range(len(pattern_list)):
            for j in range(i + 1, len(pattern_list)):
                if self.kg.has_edge(pattern_list[i], pattern_list[j]):
                    edges += 1
        
        return edges / max(possible_edges, 1)
    
    def generate_association_rules(self, min_confidence: float = 0.5) -> List[Dict]:
        """
        生成关联规则
        """
        rules = []
        patterns = self.mine_frequent_patterns()
        
        for pattern, support in patterns:
            if len(pattern) < 2:
                continue
            
            pattern_list = list(pattern)
            # 简单规则：如果A和B频繁关联，那么A -> B
            for i in range(len(pattern_list)):
                antecedent = {pattern_list[i]}
                consequent = pattern - antecedent
                if not consequent:
                    continue
                
                # 计算置信度
                confidence = self._compute_confidence(antecedent, consequent)
                if confidence >= min_confidence:
                    rules.append({
                        "antecedent": list(antecedent),
                        "consequent": list(consequent),
                        "confidence": confidence,
                        "support": support,
                        "lift": confidence / support if support > 0 else 0
                    })
        
        rules.sort(key=lambda x: -x["confidence"])
        logger.info(f"Generated {len(rules)} association rules")
        return rules[:10]  # 返回前10条
    
    def _compute_confidence(self, antecedent: Set[str], consequent: Set[str]) -> float:
        """计算规则的置信度"""
        a_node = next(iter(antecedent))
        c_node = next(iter(consequent))
        
        if self.kg.has_edge(a_node, c_node):
            edge = self.kg.get_edge(a_node, c_node)
            return edge.weight if edge else 0.0
        
        return 0.0

# ========================================
# 阶段63：权重自适应学习
# ========================================

class AdaptiveWeightLearner:
    """自适应权重学习器 - 根据使用反馈自动调整权重"""
    
    def __init__(self, kg: KnowledgeGraph, learning_rate: float = 0.1):
        self.kg = kg
        self.learning_rate = learning_rate
        self.feedback_history: List[Tuple[str, str, float, float]] = []  # (source, target, old_weight, delta)
    
    def record_feedback(self, source: str, target: str, relevance: float):
        """
        记录反馈
        relevance: 0.0-1.0，越高表示这条边越重要
        """
        edge = self.kg.get_edge(source, target)
        if not edge:
            return
        
        old_weight = edge.weight
        delta = (relevance - old_weight) * self.learning_rate
        new_weight = max(0.0, min(1.0, old_weight + delta))
        
        self.kg.update_edge_weight(source, target, new_weight)
        self.feedback_history.append((source, target, old_weight, delta))
        
        logger.debug(f"Updated weight {source}->{target}: {old_weight:.2f} -> {new_weight:.2f}")
    
    def boost_edge(self, source: str, target: str):
        """增强一条边的权重"""
        self.record_feedback(source, target, 1.0)
    
    def weaken_edge(self, source: str, target: str):
        """减弱一条边的权重"""
        self.record_feedback(source, target, 0.0)
    
    def adjust_from_clusters(self, clusters: Dict[int, Set[str]]):
        """
        根据聚类结果调整权重
        同一簇内的边权重应该更高
        """
        for cluster_nodes in clusters.values():
            node_list = list(cluster_nodes)
            for i in range(len(node_list)):
                for j in range(i + 1, len(node_list)):
                    if self.kg.has_edge(node_list[i], node_list[j]):
                        # 轻微增强同一簇内的边
                        edge = self.kg.get_edge(node_list[i], node_list[j])
                        if edge and edge.weight < 0.7:
                            new_weight = min(0.9, edge.weight + 0.1)
                            self.kg.update_edge_weight(node_list[i], node_list[j], new_weight)
    
    def get_learning_stats(self) -> Dict:
        """获取学习统计信息"""
        if not self.feedback_history:
            return {"total_updates": 0}
        
        deltas = [h[3] for h in self.feedback_history]
        return {
            "total_updates": len(self.feedback_history),
            "avg_delta": sum(deltas) / len(deltas),
            "max_delta": max(deltas),
            "min_delta": min(deltas)
        }

# ========================================
# 阶段64：知识补全推理
# ========================================

class KnowledgeCompleter:
    """知识补全器 - 预测缺失的关系和属性"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def predict_missing_edges(self, min_confidence: float = 0.5) -> List[Tuple[str, str, float]]:
        """
        预测可能缺失的边
        基于：共同邻居数量、路径存在性、聚类结果
        """
        predictions = []
        nodes = list(self.kg.nodes.keys())
        
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                source, target = nodes[i], nodes[j]
                
                if self.kg.has_edge(source, target):
                    continue
                
                confidence = self._compute_edge_confidence(source, target)
                if confidence >= min_confidence:
                    predictions.append((source, target, confidence))
        
        predictions.sort(key=lambda x: -x[2])
        logger.info(f"Predicted {len(predictions)} missing edges")
        return predictions[:20]  # 返回前20个
    
    def _compute_edge_confidence(self, source: str, target: str) -> float:
        """计算边存在的置信度"""
        # 1. 共同邻居
        neighbors1 = set(self.kg.get_neighbors(source))
        neighbors2 = set(self.kg.get_neighbors(target))
        common = len(neighbors1 & neighbors2)
        if common == 0:
            return 0.0
        
        # 2. Jaccard相似度
        jaccard = common / max(len(neighbors1 | neighbors2), 1)
        
        # 3. 路径长度（简单版本：是否有2跳路径）
        has_2hop = len(neighbors1 & neighbors2) > 0
        
        confidence = 0.7 * jaccard + (0.3 if has_2hop else 0)
        return min(1.0, confidence)
    
    def complete_attributes(self, node: str) -> Dict[str, Any]:
        """
        补全节点的缺失属性
        基于同簇节点的属性
        """
        if node not in self.kg.nodes:
            return {}
        
        current_attrs = self.kg.nodes[node].attributes or {}
        completed = current_attrs.copy()
        
        # 找相似节点
        neighbors = self.kg.get_neighbors(node)
        similar_nodes = neighbors[:5]
        
        # 收集相似节点的属性
        attr_counter = defaultdict(Counter)
        for n in similar_nodes:
            attrs = self.kg.nodes[n].attributes or {}
            for key, value in attrs.items():
                if key not in current_attrs:
                    attr_counter[key][value] += 1
        
        # 补全属性（取多数）
        for key, counter in attr_counter.items():
            if counter:
                most_common = counter.most_common(1)[0][0]
                completed[key] = most_common
                logger.debug(f"Completed attribute {key}={most_common} for {node}")
        
        return completed
    
    def auto_complete(self, auto_add: bool = True, confidence_threshold: float = 0.6) -> int:
        """
        自动补全知识图谱
        """
        count = 0
        
        # 补全边
        predictions = self.predict_missing_edges(confidence_threshold)
        for source, target, conf in predictions:
            if auto_add:
                self.kg.add_edge(source, target, "inferred", conf)
                count += 1
        
        # 补全属性
        for node in self.kg.nodes:
            completed_attrs = self.complete_attributes(node)
            if completed_attrs != self.kg.nodes[node].attributes:
                if auto_add:
                    self.kg.nodes[node].attributes = completed_attrs
                    count += 1
        
        logger.info(f"Auto-completed {count} items")
        return count

# ========================================
# 阶段65：异常知识检测
# ========================================

class AnomalyDetector:
    """异常检测器 - 检测异常的节点和关系"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def detect_anomalous_nodes(self, std_threshold: float = 2.0) -> List[Tuple[str, str, float]]:
        """
        检测异常节点
        基于：度数异常、权重分布异常
        """
        anomalies = []
        nodes = list(self.kg.nodes.keys())
        
        if not nodes:
            return []
        
        # 计算度数统计
        degrees = [len(self.kg.get_neighbors(n)) for n in nodes]
        avg_degree = sum(degrees) / len(degrees)
        std_degree = math.sqrt(sum((d - avg_degree) ** 2 for d in degrees) / len(degrees))
        
        # 检测度数异常的节点
        for node, degree in zip(nodes, degrees):
            z_score = abs(degree - avg_degree) / (std_degree if std_degree > 0 else 1)
            if z_score > std_threshold:
                if degree > avg_degree:
                    anomalies.append((node, "high_degree", z_score))
                else:
                    anomalies.append((node, "low_degree", z_score))
        
        logger.info(f"Detected {len(anomalies)} anomalous nodes")
        return anomalies
    
    def detect_anomalous_edges(self, std_threshold: float = 2.0) -> List[Tuple[str, str, str, float]]:
        """
        检测异常边
        基于：权重异常
        """
        anomalies = []
        
        if not self.kg.edges:
            return []
        
        # 计算权重统计
        weights = [e.weight for e in self.kg.edges]
        avg_weight = sum(weights) / len(weights)
        std_weight = math.sqrt(sum((w - avg_weight) ** 2 for w in weights) / len(weights))
        
        # 检测权重异常的边
        for edge in self.kg.edges:
            z_score = abs(edge.weight - avg_weight) / (std_weight if std_weight > 0 else 1)
            if z_score > std_threshold:
                if edge.weight > avg_weight:
                    anomalies.append((edge.source, edge.target, "high_weight", z_score))
                else:
                    anomalies.append((edge.source, edge.target, "low_weight", z_score))
        
        logger.info(f"Detected {len(anomalies)} anomalous edges")
        return anomalies
    
    def get_anomaly_report(self) -> Dict:
        """获取完整的异常报告"""
        node_anomalies = self.detect_anomalous_nodes()
        edge_anomalies = self.detect_anomalous_edges()
        
        return {
            "node_anomalies": node_anomalies,
            "edge_anomalies": edge_anomalies,
            "total_node_anomalies": len(node_anomalies),
            "total_edge_anomalies": len(edge_anomalies)
        }
    
    def suggest_fixes(self) -> List[str]:
        """建议修复操作"""
        fixes = []
        report = self.get_anomaly_report()
        
        for node, reason, score in report["node_anomalies"]:
            if reason == "low_degree":
                fixes.append(f"Consider adding more connections to node '{node}'")
        
        for s, t, reason, score in report["edge_anomalies"]:
            if reason == "low_weight":
                fixes.append(f"Consider reviewing edge '{s}'->'{t}' (low weight)")
        
        return fixes

# ========================================
# 阶段66：知识图谱压缩
# ========================================

class GraphCompressor:
    """知识图谱压缩器 - 合并冗余节点，聚合相似关系"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.compression_history: List[Dict] = []
    
    def find_duplicate_nodes(self, similarity_threshold: float = 0.9) -> List[Set[str]]:
        """
        寻找相似/重复的节点
        """
        duplicates = []
        visited = set()
        nodes = list(self.kg.nodes.keys())
        
        clusterer = KnowledgeClusterer(self.kg)
        
        for i in range(len(nodes)):
            if nodes[i] in visited:
                continue
            
            group = {nodes[i]}
            for j in range(i + 1, len(nodes)):
                if nodes[j] in visited:
                    continue
                
                sim = clusterer.compute_node_similarity(nodes[i], nodes[j])
                if sim >= similarity_threshold:
                    group.add(nodes[j])
                    visited.add(nodes[j])
            
            if len(group) > 1:
                duplicates.append(group)
                visited.add(nodes[i])
        
        return duplicates
    
    def merge_nodes(self, nodes_to_merge: Set[str], merged_name: Optional[str] = None) -> str:
        """
        合并多个节点为一个
        """
        if not nodes_to_merge:
            raise ValueError("No nodes to merge")
        
        if not merged_name:
            merged_name = "merged_" + "_".join(sorted(nodes_to_merge)[:2])
        
        # 收集所有属性
        merged_attrs = {}
        for node in nodes_to_merge:
            if node in self.kg.nodes:
                attrs = self.kg.nodes[node].attributes or {}
                merged_attrs.update(attrs)
        
        # 创建合并后的节点
        self.kg.add_node(merged_name, merged_attrs)
        
        # 重定向边
        for edge in list(self.kg.edges):
            # 检查是否需要重定向
            new_source = merged_name if edge.source in nodes_to_merge else edge.source
            new_target = merged_name if edge.target in nodes_to_merge else edge.target
            
            if new_source != edge.source or new_target != edge.target:
                # 移除旧边
                self.kg.remove_edge(edge.source, edge.target)
                # 添加新边（如果不存在）
                if new_source != new_target and not self.kg.has_edge(new_source, new_target):
                    self.kg.add_edge(new_source, new_target, edge.relation, edge.weight)
        
        # 删除原节点
        for node in nodes_to_merge:
            if node != merged_name and node in self.kg.nodes:
                self.kg.remove_node(node)
        
        self.compression_history.append({
            "action": "merge_nodes",
            "merged": list(nodes_to_merge),
            "into": merged_name
        })
        
        logger.info(f"Merged nodes {nodes_to_merge} into {merged_name}")
        return merged_name
    
    def aggregate_similar_edges(self, similarity_threshold: float = 0.8) -> int:
        """
        聚合相似的边（同一对节点的多条边）
        """
        count = 0
        edge_groups = defaultdict(list)
        
        # 按节点对分组
        for edge in self.kg.edges:
            key = tuple(sorted([edge.source, edge.target]))
            edge_groups[key].append(edge)
        
        # 合并同一对节点的边
        for key, edges in edge_groups.items():
            if len(edges) > 1:
                # 取权重最高的边
                best_edge = max(edges, key=lambda e: e.weight)
                # 删除其他边
                for edge in edges:
                    if edge != best_edge:
                        self.kg.remove_edge(edge.source, edge.target)
                        count += 1
        
        self.compression_history.append({
            "action": "aggregate_edges",
            "count": count
        })
        
        logger.info(f"Aggregated {count} similar edges")
        return count
    
    def compress(self, merge_threshold: float = 0.9, aggregate: bool = True) -> Dict:
        """
        完整压缩流程
        """
        stats = {
            "nodes_before": len(self.kg.nodes),
            "edges_before": len(self.kg.edges),
            "nodes_merged": 0,
            "edges_aggregated": 0
        }
        
        # 1. 合并相似节点
        duplicates = self.find_duplicate_nodes(merge_threshold)
        for group in duplicates:
            self.merge_nodes(group)
            stats["nodes_merged"] += len(group) - 1
        
        # 2. 聚合相似边
        if aggregate:
            stats["edges_aggregated"] = self.aggregate_similar_edges()
        
        stats["nodes_after"] = len(self.kg.nodes)
        stats["edges_after"] = len(self.kg.edges)
        
        logger.info(f"Compression complete: {stats}")
        return stats

# ========================================
# 阶段67：多维度权重
# ========================================

class MultiDimensionalWeight:
    """多维度权重表示"""
    
    DIMENSIONS = [
        "relevance",  # 相关性
        "frequency",  # 访问频率
        "recency",    # 近期性
        "quality",    # 质量
        "confidence"  # 置信度
    ]
    
    def __init__(self, initial_value: float = 0.5):
        self.values: Dict[str, float] = {
            dim: initial_value for dim in self.DIMENSIONS
        }
    
    def set_dimension(self, dimension: str, value: float):
        """设置单个维度的值"""
        if dimension in self.values:
            self.values[dimension] = max(0.0, min(1.0, value))
    
    def get_dimension(self, dimension: str) -> float:
        """获取单个维度的值"""
        return self.values.get(dimension, 0.0)
    
    def get_overall(self, weights: Optional[Dict[str, float]] = None) -> float:
        """
        计算综合权重
        加权平均
        """
        if not weights:
            weights = {dim: 1.0 / len(self.DIMENSIONS) for dim in self.DIMENSIONS}
        
        total = 0.0
        weight_sum = 0.0
        
        for dim, val in self.values.items():
            w = weights.get(dim, 0)
            total += val * w
            weight_sum += w
        
        return total / weight_sum if weight_sum > 0 else 0.0
    
    def to_dict(self) -> Dict:
        return self.values.copy()
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MultiDimensionalWeight":
        mdw = cls()
        for dim, val in data.items():
            mdw.set_dimension(dim, val)
        return mdw

class MultiDimensionalWeightManager:
    """多维权重管理器"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.weights: Dict[Tuple[str, str], MultiDimensionalWeight] = {}  # (source, target) -> MDW
    
    def get_weight(self, source: str, target: str) -> MultiDimensionalWeight:
        """获取多维权重"""
        key = (source, target)
        if key not in self.weights:
            # 从现有权重初始化
            edge = self.kg.get_edge(source, target)
            initial_val = edge.weight if edge else 0.5
            self.weights[key] = MultiDimensionalWeight(initial_val)
        return self.weights[key]
    
    def update_dimension(self, source: str, target: str, dimension: str, value: float):
        """更新单个维度"""
        mdw = self.get_weight(source, target)
        mdw.set_dimension(dimension, value)
        
        # 同时更新边的综合权重
        edge = self.kg.get_edge(source, target)
        if edge:
            overall = mdw.get_overall()
            self.kg.update_edge_weight(source, target, overall)
    
    def record_visit(self, source: str, target: str):
        """记录访问，更新频率和近期性"""
        mdw = self.get_weight(source, target)
        
        # 增加频率
        current_freq = mdw.get_dimension("frequency")
        mdw.set_dimension("frequency", min(1.0, current_freq + 0.1))
        
        # 更新近期性
        mdw.set_dimension("recency", 1.0)
        
        # 衰减其他边的近期性
        for key in self.weights:
            if key != (source, target):
                other = self.weights[key]
                r = other.get_dimension("recency")
                other.set_dimension("recency", max(0.0, r - 0.01))
    
    def get_top_edges(self, dimension: str = "relevance", limit: int = 10) -> List[Tuple[str, str, float]]:
        """按维度获取最高权重的边"""
        edges_with_vals = []
        
        for (s, t), mdw in self.weights.items():
            val = mdw.get_dimension(dimension)
            edges_with_vals.append((s, t, val))
        
        edges_with_vals.sort(key=lambda x: -x[2])
        return edges_with_vals[:limit]

# ========================================
# 阶段68：时间序列分析
# ========================================

class TimeSeriesPoint:
    """时间序列数据点"""
    
    def __init__(self, timestamp: datetime, node_count: int, edge_count: int):
        self.timestamp = timestamp
        self.node_count = node_count
        self.edge_count = edge_count
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "node_count": self.node_count,
            "edge_count": self.edge_count
        }

class TimeSeriesAnalyzer:
    """时间序列分析器"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.history: List[TimeSeriesPoint] = []
    
    def record_snapshot(self):
        """记录当前状态快照"""
        point = TimeSeriesPoint(
            timestamp=datetime.now(),
            node_count=len(self.kg.nodes),
            edge_count=len(self.kg.edges)
        )
        self.history.append(point)
        
        # 只保留最近1000个点
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
    
    def analyze_trend(self, window_size: int = 10) -> Dict[str, float]:
        """
        分析趋势
        返回：node_growth_rate, edge_growth_rate (变化率/快照)
        """
        if len(self.history) < window_size:
            return {"node_growth_rate": 0, "edge_growth_rate": 0}
        
        recent = self.history[-window_size:]
        node_values = [p.node_count for p in recent]
        edge_values = [p.edge_count for p in recent]
        
        # 简单线性回归斜率
        node_trend = self._compute_slope(node_values)
        edge_trend = self._compute_slope(edge_values)
        
        return {
            "node_growth_rate": node_trend,
            "edge_growth_rate": edge_trend
        }
    
    def _compute_slope(self, values: List[int]) -> float:
        """计算斜率"""
        n = len(values)
        if n < 2:
            return 0.0
        
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def predict_next(self, steps: int = 1) -> Dict[str, int]:
        """预测未来状态"""
        trend = self.analyze_trend()
        
        if not self.history:
            return {"predicted_nodes": 0, "predicted_edges": 0}
        
        current = self.history[-1]
        
        return {
            "predicted_nodes": int(current.node_count + trend["node_growth_rate"] * steps),
            "predicted_edges": int(current.edge_count + trend["edge_growth_rate"] * steps)
        }

# ========================================
# 阶段69：知识图谱索引优化
# ========================================

class GraphIndex:
    """增强的图索引"""
    
    def __init__(self):
        self.node_index: Dict[str, Node] = {}  # 节点名 -> 节点
        self.source_edge_index: Dict[str, List[Edge]] = defaultdict(list)  # 源节点 -> 边列表
        self.target_edge_index: Dict[str, List[Edge]] = defaultdict(list)  # 目标节点 -> 边列表
        self.relation_index: Dict[str, List[Edge]] = defaultdict(list)  # 关系名 -> 边列表
        self.attribute_index: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))  # 属性值 -> 节点集合
    
    def index_node(self, node: Node):
        """索引节点"""
        self.node_index[node.name] = node
        
        # 索引属性
        if node.attributes:
            for key, value in node.attributes.items():
                self.attribute_index[key][str(value)].add(node.name)
    
    def index_edge(self, edge: Edge):
        """索引边"""
        self.source_edge_index[edge.source].append(edge)
        self.target_edge_index[edge.target].append(edge)
        self.relation_index[edge.relation_name].append(edge)
    
    def remove_node(self, node_name: str):
        """移除节点索引"""
        if node_name in self.node_index:
            node = self.node_index[node_name]
            
            # 移除属性索引
            if node.attributes:
                for key, value in node.attributes.items():
                    val_str = str(value)
                    if val_str in self.attribute_index.get(key, {}):
                        self.attribute_index[key][val_str].discard(node_name)
            
            del self.node_index[node_name]
    
    def remove_edge(self, edge: Edge):
        """移除边索引"""
        if edge in self.source_edge_index.get(edge.source, []):
            self.source_edge_index[edge.source].remove(edge)
        if edge in self.target_edge_index.get(edge.target, []):
            self.target_edge_index[edge.target].remove(edge)
        if edge in self.relation_index.get(edge.relation_name, []):
            self.relation_index[edge.relation_name].remove(edge)
    
    def find_nodes_by_attribute(self, attr_key: str, attr_value: Any) -> Set[str]:
        """通过属性查找节点"""
        return self.attribute_index.get(attr_key, {}).get(str(attr_value), set())
    
    def find_edges_by_relation(self, relation: str) -> List[Edge]:
        """通过关系查找边"""
        return self.relation_index.get(relation, [])
    
    def rebuild_from_kg(self, kg: KnowledgeGraph):
        """从知识图谱重建索引"""
        self.node_index.clear()
        self.source_edge_index.clear()
        self.target_edge_index.clear()
        self.relation_index.clear()
        self.attribute_index.clear()
        
        for node in kg.nodes.values():
            self.index_node(node)
        for edge in kg.edges:
            self.index_edge(edge)

# ========================================
# 阶段70：进化策略配置
# ========================================

class EvolutionStrategy:
    """进化策略配置"""
    
    DEFAULT_CONFIG = {
        "clustering_threshold": 0.3,
        "min_support": 0.1,
        "min_confidence": 0.5,
        "learning_rate": 0.1,
        "compression_threshold": 0.9,
        "anomaly_threshold": 2.0,
        "auto_complete_threshold": 0.6,
        "weight_decay_rate": 0.01,
        "evolution_cycles": 100
    }
    
    PRESETS = {
        "conservative": {
            "clustering_threshold": 0.5,
            "min_support": 0.2,
            "min_confidence": 0.7,
            "learning_rate": 0.05,
            "auto_complete_threshold": 0.8,
            "weight_decay_rate": 0.001
        },
        "aggressive": {
            "clustering_threshold": 0.1,
            "min_support": 0.05,
            "min_confidence": 0.3,
            "learning_rate": 0.2,
            "auto_complete_threshold": 0.4,
            "weight_decay_rate": 0.02
        },
        "balanced": DEFAULT_CONFIG
    }
    
    def __init__(self, preset: str = "balanced"):
        self.config = self.DEFAULT_CONFIG.copy()
        self.apply_preset(preset)
    
    def apply_preset(self, preset: str):
        """应用预设配置"""
        if preset in self.PRESETS:
            self.config.update(self.PRESETS[preset])
            logger.info(f"Applied evolution preset: {preset}")
    
    def set_param(self, key: str, value: Any):
        """设置单个参数"""
        if key in self.config:
            self.config[key] = value
            logger.info(f"Set evolution param {key}={value}")
    
    def get_param(self, key: str) -> Any:
        """获取参数"""
        return self.config.get(key)
    
    def get_config(self) -> Dict:
        """获取完整配置"""
        return self.config.copy()

# ========================================
# 综合进化引擎
# ========================================

class EvolutionEngine:
    """综合进化引擎 - 整合所有进化功能"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.strategy = EvolutionStrategy()
        self.clusterer = KnowledgeClusterer(kg)
        self.rule_miner = AssociationRuleMiner(kg)
        self.weight_learner = AdaptiveWeightLearner(kg, self.strategy.get_param("learning_rate"))
        self.completer = KnowledgeCompleter(kg)
        self.anomaly_detector = AnomalyDetector(kg)
        self.compressor = GraphCompressor(kg)
        self.md_weight_manager = MultiDimensionalWeightManager(kg)
        self.ts_analyzer = TimeSeriesAnalyzer(kg)
        self.graph_index = GraphIndex()
        self.graph_index.rebuild_from_kg(kg)
    
    def evolve_step(self) -> Dict:
        """
        执行一步进化
        """
        logger.info("Starting evolution step...")
        
        results = {}
        
        # 1. 记录快照
        self.ts_analyzer.record_snapshot()
        
        # 2. 聚类
        clusters = self.clusterer.cluster_nodes(self.strategy.get_param("clustering_threshold"))
        results["clusters"] = len(clusters)
        
        # 3. 调整权重
        self.weight_learner.adjust_from_clusters(clusters)
        
        # 4. 挖掘规则
        rules = self.rule_miner.generate_association_rules(self.strategy.get_param("min_confidence"))
        results["rules_found"] = len(rules)
        
        # 5. 自动补全
        completed = self.completer.auto_complete(
            auto_add=True,
            confidence_threshold=self.strategy.get_param("auto_complete_threshold")
        )
        results["items_completed"] = completed
        
        # 6. 更新索引
        self.graph_index.rebuild_from_kg(self.kg)
        
        # 7. 趋势分析
        trend = self.ts_analyzer.analyze_trend()
        results.update(trend)
        
        logger.info(f"Evolution step complete: {results}")
        return results
    
    def full_evolution(self, cycles: Optional[int] = None) -> Dict:
        """
        执行完整进化流程
        """
        if cycles is None:
            cycles = self.strategy.get_param("evolution_cycles")
        
        logger.info(f"Starting full evolution ({cycles} cycles)...")
        
        summary = {
            "cycles": cycles,
            "steps": []
        }
        
        for i in range(cycles):
            step_result = self.evolve_step()
            summary["steps"].append(step_result)
        
        # 最终压缩
        compression = self.compressor.compress(self.strategy.get_param("compression_threshold"))
        summary["compression"] = compression
        
        # 最终异常检测
        anomalies = self.anomaly_detector.get_anomaly_report()
        summary["anomalies"] = anomalies
        
        logger.info("Full evolution complete")
        return summary
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        return {
            "nodes": len(self.kg.nodes),
            "edges": len(self.kg.edges),
            "clusters": len(self.clusterer.clusters),
            "evolution_strategy": self.strategy.get_config(),
            "learning_stats": self.weight_learner.get_learning_stats(),
            "trend": self.ts_analyzer.analyze_trend(),
            "anomalies": self.anomaly_detector.get_anomaly_report()
        }
