#!/usr/bin/env python3
"""
阶段10：程序基础运行测试
"""
import os
import tempfile
import time

from eternal_agent.constants import KG_SAVE_PATH
from eternal_agent.knowledge_graph import KnowledgeGraph
from eternal_agent.task_queue import BoundedTaskQueue


def test_task_queue():
    """测试任务队列"""
    print("Testing Task Queue...")
    queue = BoundedTaskQueue(max_size=5)
    
    # 测试添加任务
    assert queue.add("task1") is True
    assert queue.add("task2") is True
    assert queue.size() == 2
    
    # 测试弹出任务
    task = queue.pop()
    assert task == "task1"
    assert queue.size() == 1
    
    # 测试批量添加
    # 当前队列有1个任务（task2），还能加4个
    added = queue.batch_add(["task3", "task4", "task5", "task6", "task7"])
    assert added == 4  # 只能再加4个（1+4=5）
    assert queue.size() == 5
    
    # 测试清空
    queue.clear()
    assert queue.is_empty() is True
    print("✓ Task Queue test passed!")


def test_knowledge_graph():
    """测试知识图谱"""
    print("\nTesting Knowledge Graph...")
    
    # 使用临时文件测试 - 不预先创建文件，让KnowledgeGraph自己创建
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(save_path=temp_path)
        
        # 测试添加节点
        kg.add_node("node1")
        kg.add_node("node2")
        assert len(kg.nodes) == 2
        
        # 测试添加边
        kg.add_edge("node1", "node2", "relates_to", 0.8)
        assert len(kg.edges) == 1
        
        # 测试推演任务
        derived = kg.derive_new_tasks("node1")
        assert len(derived) == 1
        assert "知识推演任务:node2" in derived
        
        # 测试保存和加载
        kg2 = KnowledgeGraph(save_path=temp_path)
        assert len(kg2.nodes) == 2
        assert len(kg2.edges) == 1
        
        print("✓ Knowledge Graph test passed!")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def main():
    """运行所有基础测试"""
    print("=" * 50)
    print("运行基础测试")
    print("=" * 50)
    
    test_task_queue()
    test_knowledge_graph()
    
    print("\n" + "=" * 50)
    print("所有基础测试通过！✓")
    print("=" * 50)


if __name__ == "__main__":
    main()
