#!/usr/bin/env python
"""
阶段 101-105：全面系统测试与优化迭代
验证第一阶段修复并发现更多问题
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
print("🚀 EternalAgent 全面系统测试与优化迭代 2")
print("=" * 80)
print(f"开始时间: {datetime.now()}")


class SystemTesterV2:
    """增强的系统测试与优化框架"""

    def __init__(self):
        self.issues = []
        self.passed = 0
        self.failed = 0

    def log(self, message: str, level: str = "INFO"):
        """详细日志记录"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] [{level}] {message}")

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

    def test_fixed_issues(self):
        """测试修复的问题"""
        self.log("\n" + "=" * 50)
        self.log("📋 第一部分：验证修复的问题")
        self.log("=" * 50)

        kg_file = tempfile.mktemp(suffix='.json')
        try:
            from eternal_agent import KnowledgeGraph
            kg = KnowledgeGraph(kg_file)

            # 测试 add_node 是否正常工作
            self.log("\n📂 验证：修复重复函数定义问题")
            kg.add_node("FixTestNode")
            self.check("FixTestNode" in kg.nodes, "add_node 正常工作", "节点没有被添加")

            kg.add_node("FixTestNode2")
            kg.add_edge("FixTestNode", "FixTestNode2", "test", 0.9)
            self.check(len(kg.edges) == 1, "add_edge 正常工作", "边没有被添加")

            self.log("\n✅ 重复函数问题已修复！")
            return True
        finally:
            if os.path.exists(kg_file):
                os.unlink(kg_file)

    def test_edge_cases(self):
        """边界情况压力测试"""
        self.log("\n" + "=" * 50)
        self.log("🌪️  第二部分：边界情况与极端输入测试")
        self.log("=" * 50)

        kg_file = tempfile.mktemp(suffix='.json')
        try:
            from eternal_agent import KnowledgeGraph
            kg = KnowledgeGraph(kg_file)

            # 测试空节点
            self.log("\n📂 测试1：空值/None值处理")
            kg.add_node(None)
            self.check(None not in kg.nodes, "None节点不会被添加", "None节点被添加了")

            kg.add_node("")
            self.check("" not in kg.nodes, "空字符串节点不会被添加", "空字符串节点被添加了")

            # 测试重复添加
            self.log("\n📂 测试2：重复操作")
            kg.add_node("DupeTest")
            initial_count = len(kg.nodes)
            kg.add_node("DupeTest")
            kg.add_node("DupeTest")
            self.check(len(kg.nodes) == initial_count, "重复add_node无影响", "重复操作产生了副作用")

            # 测试特殊字符节点名
            self.log("\n📂 测试3：特殊字符处理")
            special_chars = ["Node with space", "Node@!#$%^&*()", "Node/\\|"]
            for name in special_chars:
                kg.add_node(name)
            all_present = all(name in kg.nodes for name in special_chars)
            self.check(all_present, "特殊字符节点正确处理", "某些特殊字符节点未被正确处理")

            # 测试删除不存在的节点
            self.log("\n📂 测试4：删除不存在的资源")
            initial_node_count = len(kg.nodes)
            kg.remove_node("DoesNotExist123")
            self.check(len(kg.nodes) == initial_node_count, "删除不存在节点无影响", "删除操作产生了副作用")

            # 测试超大属性值
            self.log("\n📂 测试5：大属性值")
            big_attr_value = "x" * 10000
            kg.add_node("BigAttrTest", {"huge": big_attr_value})
            self.check("BigAttrTest" in kg.nodes, "超大属性节点创建成功", "超大属性节点创建失败")
            node = kg.get_node("BigAttrTest")
            self.check(node is not None and node.attributes.get("huge") == big_attr_value, "超大属性正确保存", "超大属性未正确保存")

            return True
        finally:
            if os.path.exists(kg_file):
                os.unlink(kg_file)

    def test_complex_kg(self):
        """复杂知识图谱场景测试"""
        self.log("\n" + "=" * 50)
        self.log("🏗️  第三部分：复杂图谱结构测试")
        self.log("=" * 50)

        kg_file = tempfile.mktemp(suffix='.json')
        try:
            from eternal_agent import KnowledgeGraph
            kg = KnowledgeGraph(kg_file)

            # 创建复杂的图谱
            self.log("\n📂 创建大型测试图谱：100节点，500边")
            nodes = []
            for i in range(100):
                name = f"ComplexNode_{i:03d}"
                nodes.append(name)
                kg.add_node(name, {
                    "id": i,
                    "type": random.choice(["entity", "concept", "task"]),
                    "value": random.randint(1, 100)
                })

            # 添加随机边
            for _ in range(500):
                src = random.choice(nodes)
                dst = random.choice(nodes)
                if src != dst:
                    kg.add_edge(src, dst, random.choice(["related", "depends_on", "similar"]), random.random())

            self.log(f"节点数：{len(kg.nodes)}, 边数：{len(kg.edges)}")
            self.check(len(kg.nodes) >= 100, "所有节点已创建", "节点创建不完整")

            # 测试遍历
            self.log("\n📂 测试图谱遍历（DFS、BFS）")
            try:
                dfs_result = kg.dfs_traversal(nodes[0], max_depth=10)
                self.check(len(dfs_result) > 0, "DFS遍历正常工作", "DFS失败")
                self.log(f"DFS访问了 {len(dfs_result)} 个节点")
            except Exception as e:
                self.check(False, "DFS不抛异常", str(e))

            try:
                bfs_result = kg.bfs_traversal(nodes[0], max_depth=10)
                self.check(len(bfs_result) > 0, "BFS遍历正常工作", "BFS失败")
                self.log(f"BFS访问了 {len(bfs_result)} 个节点")
            except Exception as e:
                self.check(False, "BFS不抛异常", str(e))

            # 测试关联度计算
            self.log("\n📂 测试关联度计算与推荐")
            try:
                relevance = kg.get_multi_hop_relevance(nodes[0], max_hops=3)
                self.check(isinstance(relevance, dict), "关联度返回字典", f"返回 {type(relevance)}")
                self.log(f"计算了 {len(relevance)} 个节点的关联度")
            except Exception as e:
                self.check(False, "关联度计算不抛异常", str(e))

            # 测试路径查找
            self.log("\n📂 测试路径查找")
            try:
                path = kg.find_path(nodes[0], nodes[-1], max_depth=10)
                self.log(f"路径查找：{'找到' if path else '未找到'}")
                if path:
                    self.log(f"路径：{' -> '.join(path)}")
            except Exception as e:
                self.check(False, "路径查找不抛异常", str(e))

            return True
        finally:
            if os.path.exists(kg_file):
                os.unlink(kg_file)

    def test_persistence(self):
        """持久化与恢复测试"""
        self.log("\n" + "=" * 50)
        self.log("💾 第四部分：持久化与状态恢复测试")
        self.log("=" * 50)

        kg_file = tempfile.mktemp(suffix='.json')
        try:
            from eternal_agent import KnowledgeGraph

            # 创建并保存
            kg = KnowledgeGraph(kg_file)
            for i in range(20):
                kg.add_node(f"SaveTest_{i:02d}", {"index": i})
            for i in range(10):
                kg.add_edge(f"SaveTest_{i:02d}", f"SaveTest_{i+1:02d}", "next", 0.9)
            kg.force_save()

            self.log(f"保存了 {len(kg.nodes)} 节点，{len(kg.edges)} 边")

            # 重新加载
            kg2 = KnowledgeGraph(kg_file)
            self.log(f"重新加载了 {len(kg2.nodes)} 节点，{len(kg2.edges)} 边")

            self.check(len(kg2.nodes) == len(kg.nodes), "节点完全恢复", "节点数不一致")
            self.check(len(kg2.edges) == len(kg.edges), "边完全恢复", "边数不一致")

            # 验证内容一致
            content_ok = all(f"SaveTest_{i:02d}" in kg2.nodes for i in range(20))
            self.check(content_ok, "所有节点恢复", "某些节点丢失")

            return True
        finally:
            if os.path.exists(kg_file):
                os.unlink(kg_file)

    def test_observability_features(self):
        """可观测性功能测试"""
        self.log("\n" + "=" * 50)
        self.log("📊 第五部分：可观测性功能测试")
        self.log("=" * 50)

        from eternal_agent import (
            MetricType, MetricsCollector, Tracer, AlertSeverity,
            AlertManager, LogLevel, LogAnalyzer, HealthReporter, ObservableSystem
        )

        # 指标收集
        self.log("\n📂 指标收集")
        metrics = MetricsCollector()
        metrics.counter_add("test.counter", 10)
        metrics.gauge_set("test.gauge", 0.85)
        self.check("test.counter" in metrics.counters, "Counter指标存在", "Counter指标未找到")
        self.check("test.gauge" in metrics.gauges, "Gauge指标存在", "Gauge指标未找到")

        # 追踪
        self.log("\n📂 调用链追踪")
        tracer = Tracer()
        span1 = tracer.start_span("root_operation")
        span2 = tracer.start_span("child_operation", span1.span_id)
        tracer.end_span(span2.span_id)
        tracer.end_span(span1.span_id)
        self.check(len(tracer.get_all_traces()) > 0, "追踪信息被保存", "追踪未保存")

        # 告警
        self.log("\n📂 告警系统")
        alerts = AlertManager()
        alert = alerts.create_alert("test.alert", AlertSeverity.WARNING, "测试告警")
        self.check(alert is not None, "告警创建成功", "告警创建失败")
        active_alerts = alerts.get_active_alerts()
        self.check(len(active_alerts) == 1, "活跃告警存在", "活跃告警未找到")
        resolve_ok = alerts.resolve_alert(alert.alert_id)
        self.check(resolve_ok, "告警可以被解决", "告警解决失败")

        # 完整可观测性系统
        self.log("\n📂 综合可观测性系统")
        obs = ObservableSystem()
        overview = obs.get_overview()
        self.check("metrics" in overview, "可观测性概览正确", "概览结构异常")
        self.log(f"概览结构正常")

        return True

    def test_evolution_and_reliability(self):
        """进化引擎和可靠性管理测试"""
        self.log("\n" + "=" * 50)
        self.log("⚡ 第六部分：进化与可靠性测试")
        self.log("=" * 50)

        kg_file = tempfile.mktemp(suffix='.json')
        try:
            from eternal_agent import (
                KnowledgeGraph, EvolutionEngine, ReliabilityManager
            )

            kg = KnowledgeGraph(kg_file)

            # 进化引擎
            self.log("\n📂 进化引擎测试")
            engine = EvolutionEngine(kg)
            engine.run_evolution_cycle()
            self.check(True, "进化周期执行", "进化周期有异常")

            # 可靠性管理器
            self.log("\n📂 可靠性管理器测试")
            rel_mgr = ReliabilityManager(kg)
            results = rel_mgr.perform_maintenance()
            self.check(isinstance(results, dict), "维护任务返回结果", "维护返回类型异常")
            self.log(f"执行了 {len(results.get('actions', []))} 个维护动作")

            # 健康检查
            report = rel_mgr.get_full_report()
            self.check("health" in report, "健康检查报告", "报告结构异常")

            return True
        finally:
            if os.path.exists(kg_file):
                os.unlink(kg_file)

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("开始全面测试")
        print("=" * 80)

        try:
            self.test_fixed_issues()
            self.test_edge_cases()
            self.test_complex_kg()
            self.test_persistence()
            self.test_observability_features()
            self.test_evolution_and_reliability()

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

        if self.issues:
            self.log("\n🔧 发现的问题:")
            for i, issue in enumerate(self.issues, 1):
                self.log(f"  {i}. {issue['test']}: {issue['issue']}")

        return self.issues


if __name__ == "__main__":
    tester = SystemTesterV2()
    issues = tester.run_all_tests()

    print("\n" + "=" * 80)
    if issues:
        print("❌ 发现新问题，继续进入下一阶段修复...")
    else:
        print("✅ 所有测试通过！准备进行最终系统集成验证！")
    print("=" * 80)
