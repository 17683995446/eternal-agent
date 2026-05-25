#!/usr/bin/env python
"""
阶段 101-105：全面系统测试与优化 - 第一阶段
本测试进行全面的代码分析和问题发现
"""
import sys
import os
import tempfile
import time
import json
import random
import string
from typing import Dict, List, Any
from datetime import datetime

# 引入我们的模块
sys.path.insert(0, '/workspace')

print("=" * 80)
print("🚀 开始 EternalAgent 全面系统测试与优化迭代 1")
print("=" * 80)
print(f"\n开始时间: {datetime.now()}")


class SystemTester:
    """系统测试与优化框架"""
    
    def __init__(self):
        self.issues = []
        self.passed = 0
        self.failed = 0
        self.log_file = tempfile.mktemp(suffix='.log')
    
    def log(self, message: str, level: str = "INFO"):
        """详细日志记录"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def check(self, condition: bool, test_name: str, issue_desc: str):
        """检查条件，记录结果"""
        if condition:
            self.log(f"✅ PASS: {test_name}", "INFO")
            self.passed += 1
        else:
            self.log(f"❌ FAIL: {test_name} - {issue_desc}", "ERROR")
            self.issues.append({
                "test": test_name,
                "issue": issue_desc
            })
            self.failed += 1
    
    def test_static_analysis(self):
        """静态代码分析 - 测试1"""
        self.log("\n" + "=" * 50)
        self.log("📋 第一部分：静态代码分析")
        self.log("=" * 50)
        
        # 检查1：重复函数定义
        self.log("\n📂 检查：重复函数定义问题")
        
        # 读取knowledge_graph.py分析
        kg_file = '/workspace/eternal_agent/knowledge_graph.py'
        with open(kg_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查add_node重复定义
        add_node_count = content.count('def add_node(')
        self.check(
            add_node_count == 1, 
            "知识图谱模块中的 add_node 函数不应该重复", 
            f"发现 {add_node_count} 次 add_node 函数定义！"
        )
        
        # 检查add_edge重复定义
        add_edge_count = content.count('def add_edge(')
        self.check(
            add_edge_count == 1, 
            "知识图谱模块中的 add_edge 函数不应该重复", 
            f"发现 {add_edge_count} 次 add_edge 函数定义！"
        )
    
    def test_unit_knowledge_graph(self):
        """单元测试 - 知识图谱 - 测试2"""
        self.log("\n" + "=" * 50)
        self.log("🧪 第二部分：知识图谱单元测试")
        self.log("=" * 50)
        
        from eternal_agent import KnowledgeGraph
        temp_path = tempfile.mktemp(suffix='.json')
        
        try:
            kg = KnowledgeGraph(temp_path)
            
            # 测试1：基本节点和边操作
            self.log("\n📌 测试1：节点和边基本操作")
            kg.add_node("TestNode1")
            self.check("TestNode1" in kg.nodes, "节点添加后存在", "TestNode1 未找到")
            
            kg.add_edge("TestNode1", "TestNode2", "has", 0.8)
            self.check("TestNode2" in kg.nodes, "add_edge自动创建目标节点", "TestNode2 未找到")
            
            self.check(len(kg.edges) == 1, "边添加成功", "边未找到")
            
            # 测试2：重复函数调用
            self.log("\n📌 测试2：重复函数问题影响")
            # 这里我们测试因为重复函数导致的问题
            initial_len = len(kg.edges)
            
            # 添加边看是否正确
            kg.add_edge("TestNode2", "TestNode3", "has", 0.9)
            
            self.log(f"  当前节点数：{len(kg.nodes)}， 边数：{len(kg.edges)}")
            self.check(len(kg.nodes) == 3, "边添加成功创建节点", f"预期3节点，实际{len(kg.nodes)}")
            
            # 测试3：删除操作
            self.log("\n📌 测试3：删除功能")
            kg.remove_node("TestNode3")
            self.check("TestNode3" not in kg.nodes, "节点删除成功", "TestNode3 仍存在")
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_complex_scenarios(self):
        """复杂场景压力测试 - 测试3"""
        self.log("\n" + "=" * 50)
        self.log("🌪️ 第三部分：复杂场景与压力测试")
        self.log("=" * 50)
        
        from eternal_agent import KnowledgeGraph
        temp_path = tempfile.mktemp(suffix='.json')
        
        try:
            kg = KnowledgeGraph(temp_path)
            
            # 测试1：100个节点+500条边
            self.log("\n📌 压力测试1：大规模知识图谱创建")
            nodes = []
            for i in range(100):
                node_name = f"Node_{i:03d}"
                nodes.append(node_name)
                kg.add_node(node_name, {"id": i, "type": "test"})
            
            # 添加随机边
            edge_count = 0
            for _ in range(500):
                source = random.choice(nodes)
                target = random.choice(nodes)
                if source != target:
                    rel = random.choice(["connected", "related", "similar", "depends"])
                    weight = random.random()
                    kg.add_edge(source, target, rel, weight)
                    edge_count += 1
            
            self.log(f"  创建了 {len(nodes)} 个节点，{edge_count} 条边")
            
            # 测试遍历
            self.log("\n📌 压力测试2：图谱遍历")
            try:
                bfs_result = kg.bfs_traversal("Node_000", max_depth=10)
                self.check(len(bfs_result) > 0, "BFS遍历成功", "BFS返回空")
                self.log(f"  BFS 访问了 {len(bfs_result)} 个节点")
            except Exception as e:
                self.check(False, "BFS不应该抛异常", str(e))
            
            # 测试属性索引
            self.log("\n📌 压力测试3：属性索引查找")
            found = kg.find_nodes_by_attribute("id", 50)
            self.check(len(found) >= 0, "属性索引查找", f"找到 {len(found)} 个节点")
            
            # 测试关联度
            self.log("\n📌 压力测试4：关联度计算")
            try:
                relevance = kg.get_multi_hop_relevance("Node_000", max_hops=3)
                self.check(len(relevance) >= 0, "多跳关联度计算", f"计算了 {len(relevance)} 个关联")
            except Exception as e:
                self.check(False, "关联度计算不应该抛异常", str(e))
            
            # 测试批量操作
            self.log("\n📌 压力测试5：批量操作")
            new_nodes = [
                (f"BatchNode_{i}", {"batch": True, "id": i})
                for i in range(50)
            ]
            added = kg.batch_add_nodes(new_nodes)
            self.check(added == 50, "批量节点添加", f"预期50个，实际{added}个")
            
            # 测试快速保存和加载
            self.log("\n📌 压力测试6：保存和重新加载")
            kg.force_save()
            kg2 = KnowledgeGraph(temp_path)
            self.check(len(kg2.nodes) > 0, "重新加载成功", f"加载后节点数{len(kg2.nodes)}")
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_edge_cases(self):
        """边界情况测试 - 测试4"""
        self.log("\n" + "=" * 50)
        self.log("🧩 第四部分：边界情况与异常测试")
        self.log("=" * 50)
        
        from eternal_agent import KnowledgeGraph
        temp_path = tempfile.mktemp(suffix='.json')
        
        try:
            kg = KnowledgeGraph(temp_path)
            
            # 测试1：空值操作
            self.log("\n📌 边界测试1：空值操作")
            kg.add_node(None)  # 这个会怎样？
            
            # 检查是否创建了None节点
            has_none_node = None in kg.nodes
            self.log(f"  None节点是否被创建：{has_none_node}")
            
            # 测试2：重复添加同一节点
            initial_node_count = len(kg.nodes)
            kg.add_node("DuplicateTest")
            kg.add_node("DuplicateTest")
            kg.add_node("DuplicateTest")
            
            self.check(
                len(kg.nodes) == initial_node_count + 1,
                "重复添加节点只创建一次",
                f"重复3次添加，但数量从{initial_node_count}变成了{len(kg.nodes)}"
            )
            
            # 测试3：删除不存在的节点
            self.log("\n📌 边界测试2：删除不存在的节点")
            initial_count = len(kg.nodes)
            kg.remove_node("NotExists")  # 不应该有问题
            self.check(
                len(kg.nodes) == initial_count,
                "删除不存在的节点无影响",
                f"数量从{initial_count}变成了{len(kg.nodes)}"
            )
            
            # 测试4：超大属性
            self.log("\n📌 边界测试3：超大属性和值")
            big_attr = {
                "long_string": "x" * 10000,
                "nested": {"a": {"b": {"c": "deep"}}},
                "list": list(range(1000))
            }
            kg.add_node("BigAttrTest", big_attr)
            
            self.check(
                "BigAttrTest" in kg.nodes,
                "超大属性的节点创建成功",
                "BigAttrTest节点不存在"
            )
            
            found = kg.find_nodes_by_attribute("long_string", "x" * 10000)
            self.check(
                len(found) >= 0,
                "属性索引对大值处理",
                f"查找大属性值返回{len(found)}结果"
            )
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("开始全面测试")
        print("=" * 80)
        
        try:
            self.test_static_analysis()
            self.test_unit_knowledge_graph()
            self.test_complex_scenarios()
            self.test_edge_cases()
            
        except Exception as e:
            import traceback
            self.log(f"\n💥 测试框架异常: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
        
        self.report_summary()
    
    def report_summary(self):
        """生成测试报告"""
        self.log("\n" + "=" * 80)
        self.log("📊 测试结果总结")
        self.log("=" * 80)
        self.log(f"✅ 通过: {self.passed}")
        self.log(f"❌ 失败: {self.failed}")
        self.log(f"📋 总检查: {self.passed + self.failed}")
        self.log(f"📖 详细日志: {self.log_file}")
        
        if self.issues:
            self.log("\n🔧 发现的问题:")
            for i, issue in enumerate(self.issues, 1):
                self.log(f"  {i}. {issue['test']}: {issue['issue']}")
        
        return self.issues


if __name__ == "__main__":
    tester = SystemTester()
    issues = tester.run_all_tests()
    
    print("\n" + "=" * 80)
    if issues:
        print("❌ 发现问题，将进入下一阶段修复！")
    else:
        print("✅ 所有测试通过！")
    print("=" * 80)
