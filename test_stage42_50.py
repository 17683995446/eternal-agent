#!/usr/bin/env python3
"""
阶段42-50：完整运行流程测试、性能优化、配置管理、监控指标、可视化
"""
import os
import tempfile
import time
import sys

# 临时修改路径以便导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eternal_agent.agent import EternalSelfAgent
from eternal_agent.knowledge_graph import KnowledgeGraph
from eternal_agent.task_queue import GLOBAL_TASK_QUEUE, BoundedTaskQueue
from eternal_agent.config import Config, global_config
from eternal_agent.metrics import Metrics, global_metrics
from eternal_agent.utils import logger


def test_config_management():
    """阶段45：配置管理测试"""
    print("\n=== 测试配置管理 ===")
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_config_path = f.name
    
    try:
        # 测试配置创建
        config = Config(temp_config_path)
        assert config.get("loop_delay") is not None
        assert config.get("evolve_step") is not None
        
        # 测试配置修改
        original_delay = config.get("loop_delay")
        config.set("loop_delay", 0.1)
        assert config.get("loop_delay") == 0.1
        
        # 测试配置持久化
        config2 = Config(temp_config_path)
        assert config2.get("loop_delay") == 0.1
        
        # 恢复原值
        config.set("loop_delay", original_delay)
        
        print("✓ 配置管理测试通过")
        return True
    finally:
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def test_metrics_collection():
    """阶段46：监控指标测试"""
    print("\n=== 测试监控指标 ===")
    
    # 创建新的指标实例用于测试
    metrics = Metrics()
    
    # 测试指标更新
    metrics.update_task_count()
    metrics.update_task_count()
    metrics.update_node_count()
    metrics.update_edge_count()
    
    assert metrics.total_tasks_executed == 2
    assert metrics.total_nodes_added == 1
    assert metrics.total_edges_added == 1
    
    # 测试统计获取
    stats = metrics.get_stats()
    assert "uptime_seconds" in stats
    assert "total_tasks_executed" in stats
    
    print("✓ 监控指标测试通过")
    return True


def test_performance_optimization():
    """阶段43：性能优化测试"""
    print("\n=== 测试性能优化 ===")
    
    # 创建临时KG
    temp_kg_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_kg_path)
        
        # 测试批量添加
        start = time.time()
        for i in range(50):
            kg.add_node(f"perf_test_node_{i}")
            if i > 0:
                kg.add_edge(
                    f"perf_test_node_{i-1}",
                    f"perf_test_node_{i}",
                    "next",
                    0.8
                )
        end = time.time()
        
        elapsed = end - start
        print(f"  添加50个节点和49条边耗时: {elapsed:.3f}s")
        
        # 测试索引查询性能
        start = time.time()
        for i in range(50):
            edges = kg.get_edges_from(f"perf_test_node_{i}")
        end = time.time()
        
        elapsed = end - start
        print(f"  50次索引查询耗时: {elapsed:.3f}s")
        
        # 验证数据正确性
        assert len(kg.nodes) == 50
        assert len(kg.edges) == 49
        
        print("✓ 性能优化测试通过")
        return True
    finally:
        if os.path.exists(temp_kg_path):
            os.unlink(temp_kg_path)


def test_complete_workflow():
    """阶段42：完整运行流程测试"""
    print("\n=== 测试完整运行流程 ===")
    
    # 清理全局状态
    GLOBAL_TASK_QUEUE.clear()
    
    # 使用临时配置和KG
    temp_config_path = tempfile.mktemp(suffix='.json')
    temp_kg_path = tempfile.mktemp(suffix='.json')
    
    try:
        # 设置快速测试配置
        config = Config(temp_config_path)
        config.set("loop_delay", 0.05)
        config.set("evolve_step", 10)
        
        # 创建agent
        agent = EternalSelfAgent()
        agent._evolve_step = 10  # 快速进化
        agent._loop_delay = 0.05
        
        # 替换知识图谱为临时的
        agent.knowledge_graph = KnowledgeGraph(temp_kg_path)
        
        # 添加初始任务
        GLOBAL_TASK_QUEUE.add("阶段42测试任务")
        
        # 运行一小段时间
        print("  运行Agent...")
        start_time = time.time()
        while time.time() - start_time < 2 and agent.run_counter < 30:
            agent.health_check()
            task = agent.get_current_task()
            if task:
                agent.execute_task(task)
            else:
                agent.idle_self_evolve()
            time.sleep(0.01)
        
        # 验证结果
        assert agent.run_counter > 0
        stats = agent.knowledge_graph.get_stats()
        assert stats['nodes_count'] > 0
        assert stats['edges_count'] > 0
        
        print(f"  运行步数: {agent.run_counter}")
        print(f"  知识图谱: {stats['nodes_count']} 节点, {stats['edges_count']} 边")
        
        print("✓ 完整运行流程测试通过")
        return True
    finally:
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)
        if os.path.exists(temp_kg_path):
            os.unlink(temp_kg_path)


def main():
    """阶段42-50综合测试"""
    print("=" * 60)
    print("阶段42-50：系统集成与基础优化综合测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # 测试配置管理
        if not test_config_management():
            all_passed = False
        
        # 测试监控指标
        if not test_metrics_collection():
            all_passed = False
        
        # 测试性能优化
        if not test_performance_optimization():
            all_passed = False
        
        # 测试完整工作流
        if not test_complete_workflow():
            all_passed = False
        
    except Exception as e:
        print(f"\n✗ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 阶段42-50所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
