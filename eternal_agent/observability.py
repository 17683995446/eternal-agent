"""
基于第一性原理的轻量永动知识图谱Agent
阶段81-90：监控与可观测性
"""
import json
import time
import threading
import hashlib
from datetime import datetime
from collections import deque, defaultdict, Counter
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum

from .utils import logger, get_timestamp


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """指标数据结构"""
    name: str
    type: MetricType
    value: float
    timestamp: float = field(default_factory=get_timestamp)
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""


class MetricsCollector:
    """
    阶段81：指标收集系统
    
    提供全面的指标收集、导出功能
    """
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.gauges: Dict[str, float] = {}
        self.counters: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.metric_descriptions: Dict[str, str] = {}
        
    def register_metric(self, name: str, description: str = ""):
        """注册指标"""
        with self.lock:
            self.metric_descriptions[name] = description
        
    def counter_add(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """计数器递增"""
        with self.lock:
            if name not in self.counters:
                self.counters[name] = 0.0
            self.counters[name] += value
            self._record_metric(name, MetricType.COUNTER, self.counters[name], labels)
        
    def gauge_set(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置测量值"""
        with self.lock:
            self.gauges[name] = value
            self._record_metric(name, MetricType.GAUGE, value, labels)
            
    def histogram_observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """直方图观测"""
        with self.lock:
            self._record_metric(name, MetricType.HISTOGRAM, value, labels)
            
    def _record_metric(self, name: str, type: MetricType, value: float, labels: Dict[str, str] = None):
        """记录指标（内部方法）"""
        metric = Metric(
            name=name,
            type=type,
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(metric)
        
    def get_metrics(self, name: str = None) -> List[Metric]:
        """获取指标数据"""
        with self.lock:
            if name:
                return list(self.metrics.get(name, []))
            result = []
            for m_list in self.metrics.values():
                result.extend(m_list)
            return result
            
    def export_metrics(self, format: str = "json") -> str:
        """导出指标"""
        with self.lock:
            data = {
                "counters": self.counters.copy(),
                "gauges": self.gauges.copy(),
                "metrics": [asdict(m) for m in self.get_metrics()]
            }
            return json.dumps(data, indent=2)
            
    def reset_metrics(self):
        """重置所有指标"""
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()


@dataclass
class Span:
    """
    阶段82：分布式追踪
    
    调用链跟踪单元
    """
    span_id: str
    trace_id: str
    name: str
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "OK"
    
    def duration(self) -> Optional[float]:
        """获取持续时间"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        if self.duration():
            data["duration_ms"] = self.duration() * 1000
        return data


class Tracer:
    """
    阶段82：分布式追踪
    
    提供完整的调用链追踪功能
    """
    
    def __init__(self):
        self.spans: Dict[str, Span] = {}
        self.active_spans: Dict[str, List[Span]] = defaultdict(list)
        self.traces: Dict[str, List[Span]] = defaultdict(list)
        self.lock = threading.Lock()
        
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return hashlib.md5(f"{time.time()}-{id(self)}".encode()).hexdigest()
        
    def start_span(self, name: str, parent_span_id: Optional[str] = None,
                   attributes: Dict = None) -> Span:
        """开始一个新的跨度"""
        span_id = self._generate_id()
        
        if parent_span_id and parent_span_id in self.spans:
            trace_id = self.spans[parent_span_id].trace_id
        else:
            trace_id = self._generate_id()
            
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            parent_span_id=parent_span_id,
            attributes=attributes or {}
        )
        
        with self.lock:
            self.spans[span_id] = span
            self.active_spans[trace_id].append(span)
            self.traces[trace_id].append(span)
            
        return span
        
    def end_span(self, span_id: str, status: str = "OK") -> Optional[Span]:
        """结束跨度"""
        with self.lock:
            if span_id not in self.spans:
                return None
            span = self.spans[span_id]
            span.end_time = time.time()
            span.status = status
            return span
            
    def get_trace(self, trace_id: str) -> List[Span]:
        """获取完整的调用链"""
        with self.lock:
            return self.traces.get(trace_id, [])
            
    def get_all_traces(self, limit: int = 100) -> List[List[Span]]:
        """获取所有追踪记录"""
        with self.lock:
            result = []
            for trace_id, spans in list(self.traces.items())[-limit:]:
                result.append(spans)
            return result


class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


@dataclass
class Alert:
    """告警数据结构"""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    timestamp: float = field(default_factory=get_timestamp)
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertManager:
    """
    阶段83：告警系统
    
    提供告警规则、通知、历史管理
    """
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_rules: List[Dict] = []
        self.notification_handlers: List[Callable] = []
        self.alert_history: deque = deque(maxlen=1000)
        self.lock = threading.Lock()
        
    def _generate_alert_id(self) -> str:
        """生成告警ID"""
        return hashlib.md5(f"{time.time()}-alert".encode()).hexdigest()
        
    def add_rule(self, rule: Dict):
        """添加告警规则"""
        with self.lock:
            self.alert_rules.append(rule)
            
    def register_handler(self, handler: Callable):
        """注册通知处理器"""
        self.notification_handlers.append(handler)
        
    def create_alert(self, name: str, severity: AlertSeverity, message: str,
                    metadata: Dict = None) -> Alert:
        """创建告警"""
        alert_id = self._generate_alert_id()
        alert = Alert(
            alert_id=alert_id,
            name=name,
            severity=severity,
            message=message,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.alerts.append(alert)
            self.alert_history.append(asdict(alert))
            
        # 调用通知处理器
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
                
        logger.warning(f"ALERT: [{severity.value}] {name} - {message}")
        return alert
        
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = time.time()
                    logger.info(f"Alert resolved: {alert.name}")
                    return True
        return False
        
    def get_active_alerts(self) -> List[Alert]:
        """获取活动告警"""
        with self.lock:
            return [a for a in self.alerts if not a.resolved]
            
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """获取告警历史"""
        with self.lock:
            return list(self.alert_history)[-limit:]


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """日志条目"""
    level: LogLevel
    message: str
    timestamp: float = field(default_factory=get_timestamp)
    module: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class LogAnalyzer:
    """
    阶段85：日志分析
    
    提供日志聚合、搜索和异常检测
    """
    
    def __init__(self, max_logs: int = 10000):
        self.logs: deque = deque(maxlen=max_logs)
        self.log_stats: Dict = defaultdict(lambda: defaultdict(int))
        self.lock = threading.Lock()
        
    def log(self, level: LogLevel, message: str, module: str = "",
           metadata: Dict = None):
        """记录日志"""
        entry = LogEntry(
            level=level,
            message=message,
            module=module,
            metadata=metadata or {}
        )
        with self.lock:
            self.logs.append(entry)
            self.log_stats[level][module] += 1
            
    def search_logs(self, query: str = "", level: LogLevel = None,
                   module: str = "", limit: int = 100) -> List[LogEntry]:
        """搜索日志"""
        results = []
        with self.lock:
            for entry in self.logs:
                if level and entry.level != level:
                    continue
                if module and entry.module != module:
                    continue
                if query and query.lower() not in entry.message.lower():
                    continue
                results.append(entry)
                if len(results) >= limit:
                    break
        return results
        
    def get_log_stats(self) -> Dict:
        """获取日志统计"""
        with self.lock:
            return dict(self.log_stats)
            
    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict]:
        """检测日志异常"""
        anomalies = []
        stats = self.get_log_stats()
        
        # 简单的异常检测：比较最近和历史
        for level, modules in stats.items():
            for module, count in modules.items():
                if level in (LogLevel.ERROR, LogLevel.CRITICAL) and count > 5:
                    anomalies.append({
                        "level": level.value,
                        "module": module,
                        "count": count,
                        "description": f"High error count ({count}) in {module}"
                    })
        return anomalies


class Profiler:
    """
    阶段86：性能剖析
    
    分析性能热点和瓶颈
    """
    
    def __init__(self):
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.counters: Dict[str, int] = Counter()
        self.lock = threading.Lock()
        
    def profile(self, name: str) -> Callable:
        """装饰器：性能分析"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start
                    self.record_time(name, duration)
            return wrapper
        return decorator
        
    def record_time(self, name: str, duration: float):
        """记录执行时间"""
        with self.lock:
            self.timers[name].append(duration)
            self.counters[name] += 1
            
    def get_profile_report(self) -> Dict:
        """获取性能报告"""
        report = {}
        with self.lock:
            for name, times in self.timers.items():
                if times:
                    report[name] = {
                        "count": self.counters[name],
                        "avg_ms": sum(times) / len(times) * 1000,
                        "min_ms": min(times) * 1000,
                        "max_ms": max(times) * 1000,
                        "total_ms": sum(times) * 1000
                    }
        return report
        
    def find_hotspots(self, top_n: int = 10) -> List[Dict]:
        """找出热点"""
        report = self.get_profile_report()
        sorted_hotspots = sorted(report.items(),
                                 key=lambda x: x[1]['total_ms'], reverse=True)
        return [{"name": name, **data} for name, data in sorted_hotspots[:top_n]]


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    action: str
    user: str = "system"
    timestamp: float = field(default_factory=get_timestamp)
    details: Dict = field(default_factory=dict)
        
    def to_dict(self) -> Dict:
        return asdict(self)


class AuditLogger:
    """
    阶段87：审计日志
    
    操作审计和变更追踪
    """
    
    def __init__(self, max_entries: int = 10000):
        self.audit_log: deque = deque(maxlen=max_entries)
        self.action_counts: Dict[str, int] = Counter()
        self.lock = threading.Lock()
        
    def log_action(self, action: str, user: str = "system",
                 details: Dict = None):
        """记录审计操作"""
        entry = AuditLogEntry(action, user, details)
        with self.lock:
            self.audit_log.append(entry)
            self.action_counts[action] += 1
        logger.info(f"AUDIT: {user} performed {action}")
        
    def get_audit_log(self, limit: int = 100, action: str = None) -> List[AuditLogEntry]:
        """获取审计日志"""
        results = []
        with self.lock:
            for entry in self.audit_log:
                if action and entry.action != action:
                    continue
                results.append(entry)
                if len(results) >= limit:
                    break
        return results
        
    def get_action_stats(self) -> Dict[str, int]:
        """获取操作统计"""
        with self.lock:
            return dict(self.action_counts)


@dataclass
class HealthReport:
    """健康报告"""
    status: str
    score: float
    timestamp: float = field(default_factory=get_timestamp)
    components: Dict = field(default_factory=dict)
    issues: List = field(default_factory=list)
        
    def to_dict(self) -> Dict:
        return asdict(self)


class HealthReporter:
    """
    阶段88：健康报告
    
    定期健康检查和报告生成
    """
    
    def __init__(self):
        self.reports: deque = deque(maxlen=100)
        self.checks: List[Dict] = []
        self.lock = threading.Lock()
        
    def add_check(self, check_func: Callable, name: str):
        """添加健康检查"""
        self.checks.append({"name": name, "func": check_func})
        
    def run_health_check(self) -> HealthReport:
        """运行健康检查"""
        components = {}
        issues = []
        total_score = 100.0
        
        for check in self.checks:
            try:
                result = check["func"]()
                components[check["name"]] = result
                if not result.get("healthy", True):
                    issues.append({
                        "component": check["name"],
                        "issue": result.get("message", "")
                    })
                    total_score -= 20
            except Exception as e:
                issues.append({
                    "component": check["name"],
                    "issue": f"Check failed: {str(e)}"
                })
                total_score -= 20
                
        total_score = max(0, total_score)
        status = "healthy" if total_score >= 80 else \
                 "degraded" if total_score >= 50 else "unhealthy"
                 
        report = HealthReport(status, total_score, components, issues)
        
        with self.lock:
            self.reports.append(report)
        return report
        
    def get_reports(self, limit: int = 10) -> List[HealthReport]:
        """获取健康报告历史"""
        with self.lock:
            return list(self.reports)[-limit:]


class ObservableSystem:
    """
    阶段90：可观测性集成
    
    集成指标、日志、追踪为统一视图
    """
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.tracer = Tracer()
        self.alerts = AlertManager()
        self.logs = LogAnalyzer()
        self.profiler = Profiler()
        self.audit = AuditLogger()
        self.health = HealthReporter()
        
    def get_overview(self) -> Dict:
        """获取可观测性概览"""
        return {
            "timestamp": get_timestamp(),
            "metrics": {
                "gauges": len(self.metrics.gauges),
                "counters": len(self.metrics.counters),
                "total": len(self.metrics.get_metrics())
            },
            "traces": len(self.tracer.traces),
            "alerts": {
                "active": len(self.alerts.get_active_alerts()),
                "total": len(self.alerts.get_alert_history())
            },
            "logs": len(self.logs.logs),
            "audit": len(self.audit.audit_log)
        }
        
    def export_all(self) -> Dict:
        """导出所有可观测性数据"""
        return {
            "overview": self.get_overview(),
            "metrics": self.metrics.export_metrics(),
            "alerts": self.alerts.get_alert_history(),
            "health": self.health.run_health_check().to_dict()
        }
