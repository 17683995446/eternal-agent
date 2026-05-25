#!/usr/bin/env python
"""
阶段101：REST API 全面测试
测试所有API端点功能
"""
import sys
import json
import tempfile
import os
from datetime import datetime

print("=" * 80)
print("🚀 EternalAgent REST API 全面测试")
print("=" * 80)
print(f"开始时间: {datetime.now()}")


class APITester:
    """API测试器"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.issues = []

    def log(self, message: str, level: str = "INFO"):
        """日志记录"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] [{level}] {message}")

    def check(self, condition: bool, test_name: str, issue_desc: str = ""):
        """检查条件"""
        if condition:
            self.log(f"✅ PASS: {test_name}", "INFO")
            self.passed += 1
        else:
            self.log(f"❌ FAIL: {test_name} - {issue_desc}", "ERROR")
            self.failed += 1
            if issue_desc:
                self.issues.append(f"{test_name}: {issue_desc}")

    def test_api_import(self):
        """测试API导入"""
        self.log("\n📋 第一部分：API导入测试")
        try:
            from eternal_agent import (
                APIServer,
                APIResponse,
                WSGIApplication
            )
            self.check(True, "API模块导入成功")

            server = APIServer()
            self.check(server is not None, "API服务器实例化成功")
            self.log(f"API服务器创建完成，包含 {len(dir(server))} 个方法")

        except Exception as e:
            self.check(False, "API模块导入", str(e))

    def test_health_endpoint(self):
        """测试健康检查端点"""
        self.log("\n📋 第二部分：健康检查端点测试")

        from eternal_agent import APIServer
        server = APIServer()

        # 测试 /health
        response = server.handle_request("GET", "/health")
        self.check(response["status"] == "success", "健康检查返回success")
        self.check("data" in response, "健康检查包含data字段")
        self.check("uptime_seconds" in response["data"], "包含运行时间信息")

        self.log(f"健康检查响应: {response['data']}")

    def test_node_crud(self):
        """测试节点CRUD操作"""
        self.log("\n📋 第三部分：节点CRUD操作")

        from eternal_agent import APIServer
        server = APIServer()

        # 创建节点
        create_response = server.handle_request(
            "POST", "/api/nodes",
            data={
                "name": "TestAPI_Node",
                "attributes": {"type": "test", "api_test": True},
                "tags": ["api_test"]
            }
        )
        self.check(
            create_response["status"] == "success",
            "创建节点成功",
            create_response.get("message", "")
        )
        self.log(f"创建节点响应: {create_response.get('message')}")

        # 获取节点
        get_response = server.handle_request("GET", "/api/nodes/TestAPI_Node")
        self.check(
            get_response["status"] == "success",
            "获取节点成功"
        )
        self.check(
            get_response["data"]["name"] == "TestAPI_Node",
            "节点名称正确"
        )

        # 更新节点
        update_response = server.handle_request(
            "PUT", "/api/nodes/TestAPI_Node",
            data={"attributes": {"updated": True}}
        )
        self.check(
            update_response["status"] == "success",
            "更新节点成功"
        )

        # 删除节点
        delete_response = server.handle_request("DELETE", "/api/nodes/TestAPI_Node")
        self.check(
            delete_response["status"] == "success",
            "删除节点成功"
        )

    def test_edge_crud(self):
        """测试边CRUD操作"""
        self.log("\n📋 第四部分：边CRUD操作")

        from eternal_agent import APIServer
        server = APIServer()

        # 创建边（会自动创建节点）
        create_response = server.handle_request(
            "POST", "/api/edges",
            data={
                "source": "EdgeSource",
                "target": "EdgeTarget",
                "relation": "connects",
                "weight": 0.95
            }
        )
        self.check(
            create_response["status"] == "success",
            "创建边成功"
        )
        self.log(f"创建边响应: {create_response.get('message')}")

        # 获取边列表
        list_response = server.handle_request("GET", "/api/edges")
        self.check(
            list_response["status"] == "success",
            "获取边列表成功"
        )
        self.check(
            len(list_response["data"]) > 0,
            "边列表非空"
        )

        # 删除边
        delete_response = server.handle_request(
            "DELETE", "/api/edges/EdgeSource/EdgeTarget"
        )
        self.check(
            delete_response["status"] == "success",
            "删除边成功"
        )

    def test_search(self):
        """测试搜索功能"""
        self.log("\n📋 第五部分：搜索功能")

        from eternal_agent import APIServer
        server = APIServer()

        # 创建测试数据
        server.handle_request(
            "POST", "/api/nodes",
            data={
                "name": "SearchTest",
                "attributes": {"searchable": True, "value": 42}
            }
        )

        # 搜索
        search_response = server.handle_request(
            "GET", "/api/search",
            params={"key": "searchable", "value": "True"}
        )
        self.check(
            search_response["status"] == "success",
            "搜索执行成功"
        )

        # 清理
        server.handle_request("DELETE", "/api/nodes/SearchTest")

    def test_traversal(self):
        """测试遍历功能"""
        self.log("\n📋 第六部分：遍历功能")

        from eternal_agent import APIServer
        server = APIServer()

        # 创建测试图谱
        for i in range(5):
            server.handle_request(
                "POST", "/api/nodes",
                data={"name": f"TraversalNode_{i}"}
            )

        # 创建连接
        for i in range(4):
            server.handle_request(
                "POST", "/api/edges",
                data={
                    "source": f"TraversalNode_{i}",
                    "target": f"TraversalNode_{i+1}",
                    "relation": "next"
                }
            )

        # BFS遍历
        bfs_response = server.handle_request(
            "POST", "/api/traversal/bfs",
            data={"start": "TraversalNode_0", "max_depth": 10}
        )
        self.check(
            bfs_response["status"] == "success",
            "BFS遍历成功"
        )
        self.check(
            bfs_response["data"]["visited"] > 0,
            f"BFS访问了 {bfs_response['data']['visited']} 个节点"
        )

        # DFS遍历
        dfs_response = server.handle_request(
            "POST", "/api/traversal/dfs",
            data={"start": "TraversalNode_0", "max_depth": 10}
        )
        self.check(
            dfs_response["status"] == "success",
            "DFS遍历成功"
        )

    def test_path_finding(self):
        """测试路径查找"""
        self.log("\n📋 第七部分：路径查找")

        from eternal_agent import APIServer
        server = APIServer()

        # 创建链式结构
        for i in range(3):
            server.handle_request(
                "POST", "/api/edges",
                data={
                    "source": f"PathNode_{i}",
                    "target": f"PathNode_{i+1}",
                    "relation": "next"
                }
            )

        # 查找路径
        path_response = server.handle_request(
            "POST", "/api/path",
            data={"start": "PathNode_0", "end": "PathNode_2"}
        )
        self.check(
            path_response["status"] == "success",
            "路径查找成功"
        )
        self.check(
            path_response["data"]["found"] is True,
            "找到路径"
        )
        self.log(f"路径: {path_response['data']['path']}")

    def test_relevance(self):
        """测试关联度计算"""
        self.log("\n📋 第八部分：关联度计算")

        from eternal_agent import APIServer
        server = APIServer()

        # 创建关联
        server.handle_request(
            "POST", "/api/edges",
            data={"source": "RelevanceA", "target": "RelevanceB", "weight": 0.9}
        )
        server.handle_request(
            "POST", "/api/edges",
            data={"source": "RelevanceB", "target": "RelevanceC", "weight": 0.8}
        )

        # 计算关联度
        relevance_response = server.handle_request(
            "POST", "/api/relevance",
            data={"node": "RelevanceA", "max_hops": 3}
        )
        self.check(
            relevance_response["status"] == "success",
            "关联度计算成功"
        )
        self.check(
            "Relevance" in relevance_response["data"],
            "关联度结果包含数据"
        )

    def test_tags(self):
        """测试标签管理"""
        self.log("\n📋 第九部分：标签管理")

        from eternal_agent import APIServer
        server = APIServer()

        # 创建带标签的节点
        server.handle_request(
            "POST", "/api/nodes",
            data={"name": "TagTest", "tags": ["important", "test"]}
        )

        # 获取所有标签
        tags_response = server.handle_request("GET", "/api/tags")
        self.check(
            tags_response["status"] == "success",
            "获取标签列表成功"
        )

        # 按标签查找节点
        by_tag_response = server.handle_request(
            "GET", "/api/tags",
            params={"tag": "important"}
        )
        self.check(
            by_tag_response["status"] == "success",
            "按标签查找成功"
        )

        # 清理
        server.handle_request("DELETE", "/api/nodes/TagTest")

    def test_statistics(self):
        """测试统计接口"""
        self.log("\n📋 第十部分：统计接口")

        from eternal_agent import APIServer
        server = APIServer()

        # 获取统计
        stats_response = server.handle_request("GET", "/api/stats")
        self.check(
            stats_response["status"] == "success",
            "获取统计成功"
        )
        self.check(
            "nodes_count" in stats_response["data"],
            "统计包含节点数"
        )
        self.check(
            "edges_count" in stats_response["data"],
            "统计包含边数"
        )

        self.log(f"当前统计: {stats_response['data']}")

    def test_metrics(self):
        """测试指标接口"""
        self.log("\n📋 第十一部分：指标接口")

        from eternal_agent import APIServer
        server = APIServer()

        # 获取指标
        metrics_response = server.handle_request("GET", "/api/metrics")
        self.check(
            metrics_response["status"] == "success",
            "获取指标成功"
        )
        self.check(
            "overview" in metrics_response["data"],
            "指标包含概览"
        )

    def test_tracing(self):
        """测试追踪接口"""
        self.log("\n📋 第十二部分：追踪接口")

        from eternal_agent import APIServer
        server = APIServer()

        # 创建span
        span_response = server.handle_request(
            "POST", "/api/spans",
            data={"name": "test_operation"}
        )
        self.check(
            span_response["status"] == "success",
            "创建追踪span成功"
        )

        if span_response["status"] == "success":
            span_id = span_response["data"]["span_id"]

            # 结束span
            end_response = server.handle_request(
                "PUT", f"/api/spans/{span_id}",
                data={"status": "OK"}
            )
            self.check(
                end_response["status"] == "success",
                "结束追踪span成功"
            )

    def test_batch_operations(self):
        """测试批量操作"""
        self.log("\n📋 第十三部分：批量操作性能")

        from eternal_agent import APIServer
        import time

        server = APIServer()

        # 批量创建节点
        start_time = time.time()
        for i in range(20):
            server.handle_request(
                "POST", "/api/nodes",
                data={"name": f"BatchNode_{i}", "attributes": {"index": i}}
            )
        batch_time = time.time() - start_time

        self.log(f"批量创建20个节点耗时: {batch_time:.3f}s")
        self.check(batch_time < 5.0, "批量操作性能可接受")

        # 清理
        for i in range(20):
            server.handle_request("DELETE", f"/api/nodes/BatchNode_{i}")

    def test_error_handling(self):
        """测试错误处理"""
        self.log("\n📋 第十四部分：错误处理")

        from eternal_agent import APIServer
        server = APIServer()

        # 不存在的端点
        response = server.handle_request("GET", "/api/nonexistent")
        self.check(
            response["status"] == "error",
            "不存在端点返回错误"
        )
        self.check(
            response["code"] == 404,
            "返回404状态码"
        )

        # 缺少必需参数
        response = server.handle_request(
            "POST", "/api/nodes",
            data={}  # 缺少name
        )
        self.check(
            response["status"] == "error",
            "缺少参数返回错误"
        )

        # 不存在的节点
        response = server.handle_request("GET", "/api/nodes/NotExists123")
        self.check(
            response["status"] == "error",
            "不存在的节点返回错误"
        )
        self.check(
            response["code"] == 404,
            "返回404状态码"
        )

    def run_all_tests(self):
        """运行所有测试"""
        try:
            self.test_api_import()
            self.test_health_endpoint()
            self.test_node_crud()
            self.test_edge_crud()
            self.test_search()
            self.test_traversal()
            self.test_path_finding()
            self.test_relevance()
            self.test_tags()
            self.test_statistics()
            self.test_metrics()
            self.test_tracing()
            self.test_batch_operations()
            self.test_error_handling()

        except Exception as e:
            import traceback
            self.log(f"\n💥 测试框架异常: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")

        self.report_summary()

    def report_summary(self):
        """生成报告"""
        self.log("\n" + "=" * 80)
        self.log("📊 测试结果总结")
        self.log("=" * 80)
        self.log(f"✅ 通过: {self.passed}")
        self.log(f"❌ 失败: {self.failed}")
        self.log(f"📋 总测试: {self.passed + self.failed}")
        self.log(f"📈 通过率: {self.passed / (self.passed + self.failed) * 100:.1f}%")

        if self.issues:
            self.log("\n🔧 发现的问题:")
            for i, issue in enumerate(self.issues, 1):
                self.log(f"  {i}. {issue}")


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()

    print("\n" + "=" * 80)
    if tester.failed == 0:
        print("🎉 所有API测试通过！REST API已就绪！")
    else:
        print(f"⚠️  {tester.failed}个测试失败，需要修复")
    print("=" * 80)
