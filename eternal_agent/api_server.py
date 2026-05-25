"""
阶段101：REST API设计与实现
为 EternalAgent 提供完整的 RESTful API 接口
"""
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from functools import wraps
import hashlib
import threading

from .utils import logger, get_timestamp
from .knowledge_graph import KnowledgeGraph
from .agent import EternalSelfAgent
from .metrics import global_metrics
from .observability import (
    MetricsCollector,
    Tracer,
    AlertManager,
    ObservableSystem
)
from .reliability import ReliabilityManager


class APIResponse:
    """标准API响应格式"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict:
        """成功响应"""
        return {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": get_timestamp()
        }
    
    @staticmethod
    def error(message: str, code: int = 400, details: Any = None) -> Dict:
        """错误响应"""
        return {
            "status": "error",
            "message": message,
            "code": code,
            "details": details,
            "timestamp": get_timestamp()
        }
    
    @staticmethod
    def paginated(data: List, total: int, page: int = 1, page_size: int = 20) -> Dict:
        """分页响应"""
        return {
            "status": "success",
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            },
            "timestamp": get_timestamp()
        }


class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def check(self, identifier: str) -> bool:
        """检查是否允许请求"""
        with self._lock:
            now = time.time()
            if identifier not in self.requests:
                self.requests[identifier] = []
            
            # 清理过期的请求记录
            self.requests[identifier] = [
                t for t in self.requests[identifier]
                if now - t < self.window
            ]
            
            # 检查是否超限
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            # 记录请求
            self.requests[identifier].append(now)
            return True


class APIAuthenticator:
    """API认证器"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def add_api_key(self, key: str, name: str, permissions: List[str] = None):
        """添加API密钥"""
        with self._lock:
            self.api_keys[key] = {
                "name": name,
                "permissions": permissions or ["read", "write"],
                "created_at": get_timestamp()
            }
            logger.info(f"[API] Added API key for: {name}")
    
    def validate_key(self, key: str, required_permission: str = None) -> bool:
        """验证API密钥"""
        with self._lock:
            if key not in self.api_keys:
                return False
            
            if required_permission:
                return required_permission in self.api_keys[key]["permissions"]
            
            return True
    
    def generate_key(self, name: str) -> str:
        """生成新的API密钥"""
        key = hashlib.sha256(f"{name}{time.time()}".encode()).hexdigest()
        self.add_api_key(key, name)
        return key


class APIServer:
    """
    REST API 服务器
    
    提供完整的 RESTful API 接口
    """
    
    def __init__(self, kg: KnowledgeGraph = None, agent: EternalSelfAgent = None):
        logger.info("[API Server] Initializing API Server")
        
        self.kg = kg or KnowledgeGraph()
        self.agent = agent
        
        # 初始化可观测性
        self.metrics_collector = MetricsCollector()
        self.tracer = Tracer()
        self.alert_manager = AlertManager()
        self.observable = ObservableSystem()
        
        # 初始化可靠性
        if agent is None:
            self.reliability = ReliabilityManager(self.kg)
        
        # 初始化认证和限流
        self.auth = APIAuthenticator()
        self.rate_limiter = RateLimiter(max_requests=100, window=60)
        
        # 请求计数
        self.request_count = 0
        self.start_time = time.time()
        
        logger.info("[API Server] Initialization complete")
    
    def _log_request(self, method: str, path: str, status: int):
        """记录API请求"""
        self.request_count += 1
        logger.debug(f"[API] {method} {path} -> {status}")
    
    # ==========================================
    # 健康检查接口
    # ==========================================
    
    def handle_health(self) -> Dict:
        """健康检查"""
        logger.info("[API] Health check requested")
        uptime = time.time() - self.start_time
        
        return APIResponse.success({
            "status": "healthy",
            "uptime_seconds": uptime,
            "requests_count": self.request_count,
            "version": "1.0.0"
        }, "System is healthy")
    
    # ==========================================
    # 知识图谱 - 节点操作
    # ==========================================
    
    def handle_get_nodes(self, params: Dict = None) -> Dict:
        """获取所有节点"""
        logger.info("[API] Getting all nodes")
        
        page = int(params.get("page", 1)) if params else 1
        page_size = min(int(params.get("page_size", 20)), 100)
        
        all_nodes = list(self.kg.nodes.keys())
        total = len(all_nodes)
        
        start = (page - 1) * page_size
        end = start + page_size
        nodes = all_nodes[start:end]
        
        node_list = []
        for name in nodes:
            node = self.kg.nodes[name]
            node_list.append({
                "name": node.name,
                "created_at": node.created_at,
                "is_valid": node.is_valid,
                "attributes": node.attributes,
                "tags": node.tags
            })
        
        return APIResponse.paginated(node_list, total, page, page_size)
    
    def handle_get_node(self, node_name: str) -> Dict:
        """获取单个节点"""
        logger.info(f"[API] Getting node: {node_name}")
        
        node = self.kg.get_node(node_name)
        if not node:
            return APIResponse.error("Node not found", 404)
        
        # 获取相关边
        edges_from = self.kg.get_edges_from(node_name)
        edges_to = self.kg.get_edges_to(node_name)
        
        return APIResponse.success({
            "name": node.name,
            "created_at": node.created_at,
            "is_valid": node.is_valid,
            "attributes": node.attributes,
            "tags": node.tags,
            "edges_from": len(edges_from),
            "edges_to": len(edges_to)
        })
    
    def handle_create_node(self, data: Dict) -> Dict:
        """创建节点"""
        logger.info(f"[API] Creating node: {data}")
        
        name = data.get("name")
        if not name:
            return APIResponse.error("Node name is required", 400)
        
        attributes = data.get("attributes", {})
        
        self.kg.add_node(name, attributes)
        
        # 如果有标签，添加标签
        tags = data.get("tags", [])
        for tag in tags:
            self.kg.add_tag(name, tag)
        
        self.metrics_collector.counter_add("api.nodes.created")
        
        return APIResponse.success({
            "name": name,
            "attributes": attributes,
            "tags": tags
        }, "Node created successfully")
    
    def handle_update_node(self, node_name: str, data: Dict) -> Dict:
        """更新节点"""
        logger.info(f"[API] Updating node: {node_name}")
        
        if node_name not in self.kg.nodes:
            return APIResponse.error("Node not found", 404)
        
        # 更新属性
        attributes = data.get("attributes", {})
        for key, value in attributes.items():
            self.kg.update_node_attribute(node_name, key, value)
        
        # 更新标签
        tags = data.get("tags")
        if tags is not None:
            for tag in tags:
                self.kg.add_tag(node_name, tag)
        
        self.metrics_collector.counter_add("api.nodes.updated")
        
        return APIResponse.success({
            "name": node_name,
            "attributes": attributes
        }, "Node updated successfully")
    
    def handle_delete_node(self, node_name: str) -> Dict:
        """删除节点"""
        logger.info(f"[API] Deleting node: {node_name}")
        
        if node_name not in self.kg.nodes:
            return APIResponse.error("Node not found", 404)
        
        self.kg.remove_node(node_name)
        self.metrics_collector.counter_add("api.nodes.deleted")
        
        return APIResponse.success(message="Node deleted successfully")
    
    # ==========================================
    # 知识图谱 - 边操作
    # ==========================================
    
    def handle_get_edges(self, params: Dict = None) -> Dict:
        """获取所有边"""
        logger.info("[API] Getting all edges")
        
        page = int(params.get("page", 1)) if params else 1
        page_size = min(int(params.get("page_size", 20)), 100)
        
        total = len(self.kg.edges)
        start = (page - 1) * page_size
        end = start + page_size
        
        edge_list = []
        for edge in self.kg.edges[start:end]:
            edge_list.append({
                "source": edge.source,
                "target": edge.target,
                "relation": edge.relation_name,
                "weight": edge.weight,
                "created_at": edge.created_at,
                "use_count": edge.use_count
            })
        
        return APIResponse.paginated(edge_list, total, page, page_size)
    
    def handle_create_edge(self, data: Dict) -> Dict:
        """创建边"""
        logger.info(f"[API] Creating edge: {data}")
        
        source = data.get("source")
        target = data.get("target")
        relation = data.get("relation", "related")
        weight = float(data.get("weight", 0.8))
        
        if not source or not target:
            return APIResponse.error("Source and target are required", 400)
        
        if weight < 0 or weight > 1:
            return APIResponse.error("Weight must be between 0 and 1", 400)
        
        self.kg.add_edge(source, target, relation, weight)
        self.metrics_collector.counter_add("api.edges.created")
        
        return APIResponse.success({
            "source": source,
            "target": target,
            "relation": relation,
            "weight": weight
        }, "Edge created successfully")
    
    def handle_delete_edge(self, source: str, target: str) -> Dict:
        """删除边"""
        logger.info(f"[API] Deleting edge: {source} -> {target}")
        
        edge = self.kg.get_edge(source, target)
        if not edge:
            return APIResponse.error("Edge not found", 404)
        
        self.kg.remove_edge(source, target)
        self.metrics_collector.counter_add("api.edges.deleted")
        
        return APIResponse.success(message="Edge deleted successfully")
    
    # ==========================================
    # 查询与搜索
    # ==========================================
    
    def handle_search_nodes(self, params: Dict) -> Dict:
        """搜索节点"""
        logger.info(f"[API] Searching nodes: {params}")
        
        key = params.get("key")
        value = params.get("value")
        
        if not key:
            return APIResponse.error("Search key is required", 400)
        
        results = self.kg.find_nodes_by_attribute(key, value)
        
        self.metrics_collector.counter_add("api.searches")
        
        return APIResponse.success({
            "key": key,
            "value": value,
            "count": len(results),
            "results": results
        })
    
    def handle_get_neighbors(self, node_name: str, params: Dict = None) -> Dict:
        """获取节点邻居"""
        logger.info(f"[API] Getting neighbors of: {node_name}")
        
        if node_name not in self.kg.nodes:
            return APIResponse.error("Node not found", 404)
        
        neighbors = self.kg.get_neighbors(node_name)
        
        return APIResponse.success({
            "node": node_name,
            "neighbors": neighbors,
            "count": len(neighbors)
        })
    
    # ==========================================
    # 图谱遍历与关联度
    # ==========================================
    
    def handle_dfs_traversal(self, data: Dict) -> Dict:
        """深度优先遍历"""
        logger.info(f"[API] DFS traversal: {data}")
        
        start = data.get("start")
        max_depth = int(data.get("max_depth", 10))
        
        if not start:
            return APIResponse.error("Start node is required", 400)
        
        if start not in self.kg.nodes:
            return APIResponse.error("Start node not found", 404)
        
        result = self.kg.dfs_traversal(start, max_depth)
        
        self.metrics_collector.counter_add("api.traversals.dfs")
        
        return APIResponse.success({
            "start": start,
            "max_depth": max_depth,
            "visited": len(result),
            "path": result
        })
    
    def handle_bfs_traversal(self, data: Dict) -> Dict:
        """广度优先遍历"""
        logger.info(f"[API] BFS traversal: {data}")
        
        start = data.get("start")
        max_depth = int(data.get("max_depth", 10))
        
        if not start:
            return APIResponse.error("Start node is required", 400)
        
        if start not in self.kg.nodes:
            return APIResponse.error("Start node not found", 404)
        
        result = self.kg.bfs_traversal(start, max_depth)
        
        self.metrics_collector.counter_add("api.traversals.bfs")
        
        return APIResponse.success({
            "start": start,
            "max_depth": max_depth,
            "visited": len(result),
            "path": result
        })
    
    def handle_find_path(self, data: Dict) -> Dict:
        """查找路径"""
        logger.info(f"[API] Finding path: {data}")
        
        start = data.get("start")
        end = data.get("end")
        max_depth = int(data.get("max_depth", 10))
        
        if not start or not end:
            return APIResponse.error("Start and end nodes are required", 400)
        
        if start not in self.kg.nodes or end not in self.kg.nodes:
            return APIResponse.error("Start or end node not found", 404)
        
        path = self.kg.find_path(start, end, max_depth)
        
        self.metrics_collector.counter_add("api.paths.found")
        
        return APIResponse.success({
            "start": start,
            "end": end,
            "path": path,
            "found": path is not None
        })
    
    def handle_multi_hop_relevance(self, data: Dict) -> Dict:
        """多跳关联度计算"""
        logger.info(f"[API] Multi-hop relevance: {data}")
        
        node = data.get("node")
        max_hops = int(data.get("max_hops", 3))
        
        if not node:
            return APIResponse.error("Node is required", 400)
        
        if node not in self.kg.nodes:
            return APIResponse.error("Node not found", 404)
        
        relevance = self.kg.get_multi_hop_relevance(node, max_hops)
        
        self.metrics_collector.counter_add("api.relevance.computed")
        
        return APIResponse.success({
            "node": node,
            "max_hops": max_hops,
            "relevance": relevance
        })
    
    def handle_get_recommendations(self, data: Dict) -> Dict:
        """获取推荐"""
        logger.info(f"[API] Getting recommendations: {data}")
        
        node = data.get("node")
        top_k = int(data.get("top_k", 5))
        
        if not node:
            return APIResponse.error("Node is required", 400)
        
        if node not in self.kg.nodes:
            return APIResponse.error("Node not found", 404)
        
        recommendations = self.kg.get_recommendations(node, top_k)
        
        self.metrics_collector.counter_add("api.recommendations")
        
        return APIResponse.success({
            "node": node,
            "top_k": top_k,
            "recommendations": recommendations
        })
    
    # ==========================================
    # 标签管理
    # ==========================================
    
    def handle_get_tags(self, params: Dict = None) -> Dict:
        """获取所有标签"""
        logger.info("[API] Getting all tags")
        
        tag = params.get("tag") if params else None
        
        if tag:
            nodes = self.kg.get_nodes_by_tag(tag)
            return APIResponse.success({
                "tag": tag,
                "nodes": nodes,
                "count": len(nodes)
            })
        else:
            stats = self.kg.get_tag_statistics()
            return APIResponse.success({
                "tags": stats,
                "total_tags": len(stats)
            })
    
    def handle_add_tag(self, data: Dict) -> Dict:
        """添加标签"""
        logger.info(f"[API] Adding tag: {data}")
        
        node = data.get("node")
        tag = data.get("tag")
        
        if not node or not tag:
            return APIResponse.error("Node and tag are required", 400)
        
        if node not in self.kg.nodes:
            return APIResponse.error("Node not found", 404)
        
        self.kg.add_tag(node, tag)
        
        return APIResponse.success({
            "node": node,
            "tag": tag
        }, "Tag added successfully")
    
    # ==========================================
    # 统计与元数据
    # ==========================================
    
    def handle_get_stats(self) -> Dict:
        """获取图谱统计"""
        logger.info("[API] Getting statistics")
        
        stats = self.kg.get_stats()
        
        # 添加更多统计信息
        total_edges = len(self.kg.edges)
        total_nodes = len(self.kg.nodes)
        
        stats.update({
            "total_tags": len(self.kg.get_tag_statistics()),
            "avg_degree": (total_edges * 2 / total_nodes) if total_nodes > 0 else 0,
            "api_requests": self.request_count,
            "uptime_seconds": time.time() - self.start_time
        })
        
        return APIResponse.success(stats)
    
    def handle_get_history(self, params: Dict = None) -> Dict:
        """获取历史记录"""
        logger.info("[API] Getting history")
        
        limit = int(params.get("limit", 100)) if params else 100
        limit = min(limit, 1000)
        
        history = self.kg.get_recent_history(limit)
        
        return APIResponse.success({
            "count": len(history),
            "records": history
        })
    
    # ==========================================
    # 可靠性操作
    # ==========================================
    
    def handle_backup(self) -> Dict:
        """创建备份"""
        logger.info("[API] Creating backup")
        
        try:
            backup = self.reliability.backup_manager.create_backup(
                self.kg,
                description="API backup",
                force=True
            )
            
            if backup:
                return APIResponse.success({
                    "backup_id": backup.backup_id,
                    "timestamp": backup.timestamp,
                    "size": backup.size
                }, "Backup created successfully")
            else:
                return APIResponse.error("Backup creation failed", 500)
        except Exception as e:
            logger.error(f"[API] Backup failed: {e}")
            return APIResponse.error(f"Backup failed: {str(e)}", 500)
    
    def handle_health_check(self) -> Dict:
        """健康检查"""
        logger.info("[API] Health check")
        
        try:
            report = self.reliability.get_full_report()
            return APIResponse.success(report)
        except Exception as e:
            logger.error(f"[API] Health check failed: {e}")
            return APIResponse.error(f"Health check failed: {str(e)}", 500)
    
    def handle_maintenance(self) -> Dict:
        """执行维护"""
        logger.info("[API] Running maintenance")
        
        try:
            results = self.reliability.perform_maintenance()
            return APIResponse.success(results, "Maintenance completed")
        except Exception as e:
            logger.error(f"[API] Maintenance failed: {e}")
            return APIResponse.error(f"Maintenance failed: {str(e)}", 500)
    
    # ==========================================
    # 可观测性
    # ==========================================
    
    def handle_get_metrics(self) -> Dict:
        """获取指标"""
        logger.info("[API] Getting metrics")
        
        overview = self.observable.get_overview()
        metrics = self.observable.metrics.export_metrics()
        
        return APIResponse.success({
            "overview": overview,
            "metrics": json.loads(metrics)
        })
    
    def handle_get_traces(self) -> Dict:
        """获取追踪记录"""
        logger.info("[API] Getting traces")
        
        traces = self.observable.tracer.get_all_traces(limit=50)
        
        traces_data = []
        for trace in traces:
            trace_info = {
                "trace_id": trace[0].trace_id if trace else None,
                "spans": len(trace),
                "duration_ms": sum(s.duration() or 0 for s in trace) * 1000
            }
            traces_data.append(trace_info)
        
        return APIResponse.success({
            "count": len(traces_data),
            "traces": traces_data
        })
    
    def handle_create_span(self, data: Dict) -> Dict:
        """创建追踪span"""
        logger.debug(f"[API] Creating span: {data}")
        
        name = data.get("name")
        parent_id = data.get("parent_span_id")
        
        span = self.observable.tracer.start_span(name, parent_id)
        
        return APIResponse.success({
            "span_id": span.span_id,
            "trace_id": span.trace_id
        }, "Span created")
    
    def handle_end_span(self, span_id: str, data: Dict) -> Dict:
        """结束追踪span"""
        logger.debug(f"[API] Ending span: {span_id}")
        
        status = data.get("status", "OK")
        span = self.observable.tracer.end_span(span_id, status)
        
        if not span:
            return APIResponse.error("Span not found", 404)
        
        return APIResponse.success({
            "span_id": span.span_id,
            "duration_ms": span.duration() * 1000 if span.duration() else None
        }, "Span ended")
    
    # ==========================================
    # 完整的请求处理
    # ==========================================
    
    def handle_request(self, method: str, path: str, data: Dict = None, params: Dict = None, headers: Dict = None) -> Dict:
        """
        处理完整的API请求
        
        这是API服务器的中央调度器
        """
        logger.info(f"[API] {method} {path}")
        
        # 速率限制检查
        client_id = headers.get("X-API-Key", "anonymous") if headers else "anonymous"
        if not self.rate_limiter.check(client_id):
            return APIResponse.error("Rate limit exceeded", 429)
        
        # 追踪请求
        span = self.tracer.start_span(f"{method} {path}")
        
        try:
            # 路由处理
            response = self._route(method, path, data, params)
            
            # 结束追踪
            self.tracer.end_span(span.span_id, "OK")
            
            # 记录日志
            self._log_request(method, path, response.get("code", 200))
            
            return response
            
        except Exception as e:
            logger.error(f"[API] Error handling request: {e}")
            self.tracer.end_span(span.span_id, "ERROR")
            self._log_request(method, path, 500)
            return APIResponse.error(f"Internal error: {str(e)}", 500)
    
    def _route(self, method: str, path: str, data: Dict = None, params: Dict = None) -> Dict:
        """路由分发"""
        if data is None:
            data = {}
        if params is None:
            params = {}
        
        # 健康检查
        if path == "/health" or path == "/api/health":
            return self.handle_health()
        
        # 统计
        if path == "/api/stats":
            return self.handle_get_stats()
        
        # 历史
        if path == "/api/history":
            return self.handle_get_history(params)
        
        # 指标
        if path == "/api/metrics":
            return self.handle_get_metrics()
        
        # 追踪
        if path == "/api/traces":
            return self.handle_get_traces()
        
        # 备份
        if path == "/api/backup" and method == "POST":
            return self.handle_backup()
        
        # 健康检查
        if path == "/api/health/detailed":
            return self.handle_health_check()
        
        # 维护
        if path == "/api/maintenance":
            return self.handle_maintenance()
        
        # 节点操作
        if path == "/api/nodes":
            if method == "GET":
                return self.handle_get_nodes(params)
            elif method == "POST":
                return self.handle_create_node(data)
        
        # 单个节点操作
        if path.startswith("/api/nodes/"):
            node_name = path[11:]  # 去掉 "/api/nodes/" (11个字符)
            
            # 标签操作 - 路径格式: /api/nodes/{name}/tags
            if path.endswith("/tags"):
                node_name = path[11:path.rfind("/")]
                if method == "GET":
                    return self.handle_get_tags({"node": node_name})
                elif method == "POST":
                    return self.handle_add_tag(data)
            
            # 邻居 - 路径格式: /api/nodes/{name}/neighbors
            if path.endswith("/neighbors"):
                node_name = path[11:path.rfind("/")]
                return self.handle_get_neighbors(node_name, params)
            
            # 基本CRUD
            if method == "GET":
                return self.handle_get_node(node_name)
            elif method == "PUT":
                return self.handle_update_node(node_name, data)
            elif method == "DELETE":
                return self.handle_delete_node(node_name)
        
        # 边操作
        if path == "/api/edges":
            if method == "GET":
                return self.handle_get_edges(params)
            elif method == "POST":
                return self.handle_create_edge(data)
        
        # 单个边操作
        if path.startswith("/api/edges/") and method == "DELETE":
            parts = path[11:].split("/")
            if len(parts) == 2:
                return self.handle_delete_edge(parts[0], parts[1])
        
        # 搜索
        if path == "/api/search" and method == "GET":
            return self.handle_search_nodes(params)
        
        # 遍历
        if path == "/api/traversal/dfs" and method == "POST":
            return self.handle_dfs_traversal(data)
        
        if path == "/api/traversal/bfs" and method == "POST":
            return self.handle_bfs_traversal(data)
        
        if path == "/api/path" and method == "POST":
            return self.handle_find_path(data)
        
        # 关联度
        if path == "/api/relevance" and method == "POST":
            return self.handle_multi_hop_relevance(data)
        
        if path == "/api/recommendations" and method == "POST":
            return self.handle_get_recommendations(data)
        
        # 标签
        if path == "/api/tags":
            return self.handle_get_tags(params)
        
        # 追踪span
        if path == "/api/spans" and method == "POST":
            return self.handle_create_span(data)
        
        if path.startswith("/api/spans/") and method == "PUT":
            span_id = path[11:]
            return self.handle_end_span(span_id, data or {})
        
        # 404
        return APIResponse.error("Endpoint not found", 404)


# 简单的WSGI应用接口
class WSGIApplication:
    """WSGI应用封装"""
    
    def __init__(self, api_server: APIServer = None):
        self.api_server = api_server or APIServer()
    
    def __call__(self, environ, start_response):
        """WSGI接口"""
        method = environ.get('REQUEST_METHOD', 'GET')
        path = environ.get('PATH_INFO', '/')
        
        # 解析查询参数
        from urllib.parse import parse_qs
        query_string = environ.get('QUERY_STRING', '')
        params = parse_qs(query_string)
        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        
        # 读取请求体
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        if content_length > 0:
            import sys
            body = sys.stdin.read(content_length)
            data = json.loads(body) if body else None
        else:
            data = None
        
        # 获取头部
        headers = {
            k.replace('HTTP_', ''): v
            for k, v in environ.items()
            if k.startswith('HTTP_')
        }
        
        # 处理请求
        response = self.api_server.handle_request(method, path, data, params, headers)
        
        # 生成响应
        status = response.get('code', 200)
        status_text = 'OK' if status < 400 else 'ERROR'
        response_body = json.dumps(response, ensure_ascii=False)
        
        start_response(f"{status} {status_text}", [
            ('Content-Type', 'application/json; charset=utf-8'),
            ('Content-Length', str(len(response_body)))
        ])
        
        return [response_body.encode('utf-8')]
