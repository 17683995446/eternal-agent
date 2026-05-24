#!/usr/bin/env python3
"""
阶段51-60：功能增强与扩展测试
- 阶段51：节点属性扩展
- 阶段52：边权重动态调整
- 阶段53：多类型任务支持
- 阶段54：任务优先级机制
- 阶段55：知识图谱遍历算法
- 阶段56：关联度计算增强
- 阶段57：节点分类与标签
- 阶段58：知识回溯功能
- 阶段59：批量操作优化
- 阶段60：LRU缓存机制
"""
import os
import tempfile
import time
import sys

# 临时修改路径以便导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eternal_agent.knowledge_graph import KnowledgeGraph
from eternal_agent.advanced import (
    TaskType,
    TypedTask,
    PriorityQueue,
    WeightManager,
    LRUCache,
    TagManager
)


def test_stage51_node_attributes():
    """阶段51：节点属性扩展测试"""
    print("\n=== 阶段51：节点属性扩展 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        
        # 添加带属性的节点
        kg.add_node("user_1", {"name": "Alice", "age": 30, "role": "admin"})
        kg.add_node("user_2", {"name": "Bob", "age": 25, "role": "user"})
        kg.add_node("user_3", {"name": "Charlie", "age": 35, "role": "admin"})
        
        # 更新属性
        kg.update_node_attribute("user_1", "age", 31)
        
        # 按属性查找
        admins = kg.find_nodes_by_attribute("role", "admin")
        assert len(admins) == 2
        assert "user_1" in admins
        assert "user_3" in admins
        
        print("✓ 节点属性扩展测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage52_weight_management():
    """阶段52：边权重动态调整测试"""
    print("\n=== 阶段52：边权重动态调整 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        
        # 添加边
        kg.add_edge("A", "B", "relates_to", 0.5)
        
        # 记录使用（应该强化权重）
        kg.record_edge_usage("A", "B")
        
        # 获取边
        edges = kg.get_edges_from("A")
        assert len(edges) == 1
        original_weight = edges[0].weight
        
        # 权重应该被强化
        assert original_weight > 0.5
        
        # 测试权重管理器
        wm = WeightManager()
        w1 = wm.decay(0.8)
        assert w1 < 0.8
        
        w2 = wm.boost(0.8)
        assert w2 > 0.8
        
        w3 = wm.normalize([0.2, 0.3, 0.5])
        assert abs(sum(w3) - 1.0) < 0.001
        
        print("✓ 边权重动态调整测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage53_54_task_priority():
    """阶段53-54：多类型任务和优先级队列测试"""
    print("\n=== 阶段53-54：多类型任务与优先级 ===")
    
    # 创建优先级队列
    pq = PriorityQueue(max_size=5)
    
    # 添加不同优先级的任务
    pq.add(TypedTask("low", TaskType.SYSTEM_MAINTENANCE, priority=1))
    pq.add(TypedTask("high", TaskType.KNOWLEDGE_EVOLUTION, priority=10))
    pq.add(TypedTask("medium", TaskType.KNOWLEDGE_DISCOVERY, priority=5))
    
    # 应该先获取高优先级
    task1 = pq.pop()
    assert task1 is not None
    assert task1.priority == 10
    
    task2 = pq.pop()
    assert task2 is not None
    assert task2.priority == 5
    
    print("✓ 多类型任务和优先级队列测试通过")
    return True


def test_stage55_traversal():
    """阶段55：知识图谱遍历算法测试"""
    print("\n=== 阶段55：知识图谱遍历算法 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        
        # 构建一个图：A -> B -> C -> D
        kg.add_edge("A", "B", "next", 0.8)
        kg.add_edge("B", "C", "next", 0.8)
        kg.add_edge("C", "D", "next", 0.8)
        
        # 测试DFS
        dfs_path = kg.dfs_traversal("A", max_depth=4)
        assert "A" in dfs_path
        assert "D" in dfs_path
        
        # 测试BFS
        bfs_path = kg.bfs_traversal("A", max_depth=4)
        assert "A" in bfs_path
        assert "D" in bfs_path
        
        # 测试路径查找
        path = kg.find_path("A", "D")
        assert path is not None
        assert path[0] == "A"
        assert path[-1] == "D"
        
        print("✓ 知识图谱遍历算法测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage56_relevance():
    """阶段56：关联度计算增强测试"""
    print("\n=== 阶段56：关联度计算增强 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        
        # 构建图
        kg.add_edge("A", "B", "relates_to", 0.9)
        kg.add_edge("B", "C", "relates_to", 0.8)
        kg.add_edge("A", "D", "relates_to", 0.7)
        
        # 计算多跳关联度
        relevance = kg.get_multi_hop_relevance("A", max_hops=2)
        assert "B" in relevance
        assert "C" in relevance
        
        # 获取推荐
        recs = kg.get_recommendations("A", top_k=3)
        assert len(recs) >= 1
        
        print("✓ 关联度计算增强测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage57_tags():
    """阶段57：节点分类与标签测试"""
    print("\n=== 阶段57：节点分类与标签 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        
        # 添加节点和标签
        kg.add_node("doc1")
        kg.add_node("doc2")
        kg.add_node("doc3")
        
        kg.add_tag("doc1", "technology")
        kg.add_tag("doc1", "ai")
        kg.add_tag("doc2", "technology")
        kg.add_tag("doc3", "finance")
        
        # 按标签查找
        tech_docs = kg.get_nodes_by_tag("technology")
        assert len(tech_docs) == 2
        assert "doc1" in tech_docs
        assert "doc2" in tech_docs
        
        # 获取标签统计
        stats = kg.get_tag_statistics()
        assert "technology" in stats
        assert stats["technology"] == 2
        
        print("✓ 节点分类与标签测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage58_history():
    """阶段58：知识回溯功能测试"""
    print("\n=== 阶段58：知识回溯功能 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        
        # 做一些操作
        kg.add_node("A")
        kg.add_node("B")
        kg.add_edge("A", "B", "relates_to", 0.8)
        
        # 获取历史
        history = kg.get_node_history("A")
        assert len(history) >= 1
        
        recent = kg.get_recent_history(limit=10)
        assert len(recent) >= 2
        
        print("✓ 知识回溯功能测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage59_batch_operations():
    """阶段59：批量操作优化测试"""
    print("\n=== 阶段59：批量操作优化 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        
        # 批量添加节点
        nodes_to_add = [
            (f"node_{i}", {"id": i}) for i in range(10)
        ]
        count = kg.batch_add_nodes(nodes_to_add)
        assert count == 10
        
        # 批量添加边
        edges_to_add = [
            (f"node_{i}", f"node_{i+1}", "next", 0.8) for i in range(9)
        ]
        count = kg.batch_add_edges(edges_to_add)
        assert count == 9
        
        # 验证
        assert len(kg.nodes) == 10
        assert len(kg.edges) == 9
        
        print("✓ 批量操作优化测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage60_lru_cache():
    """阶段60：LRU缓存机制测试"""
    print("\n=== 阶段60：LRU缓存机制 ===")
    
    cache = LRUCache(capacity=3)
    
    # 添加缓存
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    
    assert cache.get("a") == 1
    assert cache.size() == 3
    
    # 访问a，让a成为最新的
    cache.get("a")
    
    # 添加第四个，应该淘汰最久未使用的（b）
    cache.put("d", 4)
    
    # b 应该被淘汰
    assert cache.get("b") is None
    
    # a, c, d 应该还在
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4
    assert cache.size() == 3
    
    print("✓ LRU缓存机制测试通过")
    return True


def main():
    """阶段51-60综合测试"""
    print("=" * 60)
    print("阶段51-60：功能增强与扩展综合测试")
    print("=" * 60)
    
    all_passed = True
    tests = [
        ("节点属性扩展", test_stage51_node_attributes),
        ("边权重动态调整", test_stage52_weight_management),
        ("多类型任务与优先级", test_stage53_54_task_priority),
        ("知识图谱遍历算法", test_stage55_traversal),
        ("关联度计算增强", test_stage56_relevance),
        ("节点分类与标签", test_stage57_tags),
        ("知识回溯功能", test_stage58_history),
        ("批量操作优化", test_stage59_batch_operations),
        ("LRU缓存机制", test_stage60_lru_cache),
    ]
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 阶段51-60所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
