"""
阶段81-90：监控与可观测性综合测试
"""
import tempfile
import time
import json
from eternal_agent import (
    KnowledgeGraph,
    MetricType,
    Metric,
    MetricsCollector,
    Span,
    Tracer,
    AlertSeverity,
    Alert,
    AlertManager,
    LogLevel,
    LogEntry,
    LogAnalyzer,
    Profiler,
    AuditLogger,
    HealthReporter,
    ObservableSystem
)


def test_stage81_metrics():
    """阶段81：指标收集系统测试"""
    print("\n=== 阶段81：指标收集系统 ===")
    collector = MetricsCollector()
    collector.register_metric("test_counter", "A test counter")
    
    collector.counter_add("test_counter")
    collector.counter_add("test_counter", 2.5)
    collector.gauge_set("test_gauge", 42.0)
    collector.histogram_observe("test_histogram", 100.0)
    
    metrics = collector.get_metrics()
    print(f"Collected {len(metrics)} metrics")
    assert len(collector.counters) == 1
    assert collector.counters["test_counter"] == 3.5
    assert collector.gauges["test_gauge"] == 42.0
    
    exported = json.loads(collector.export_metrics())
    print(f"Exported metrics contains {len(exported['counters'])} counters")
    print("✓ 指标收集系统测试通过")
    return True


def test_stage82_tracing():
    """阶段82：分布式追踪测试"""
    print("\n=== 阶段82：分布式追踪 ===")
    tracer = Tracer()
    
    span1 = tracer.start_span("parent_span")
    span2 = tracer.start_span("child_span", span1.span_id, {"key": "value"})
    
    time.sleep(0.01)
    tracer.end_span(span2.span_id)
    tracer.end_span(span1.span_id)
    
    trace = tracer.get_trace(span1.trace_id)
    print(f"Found {len(trace)} spans in trace")
    assert len(trace) == 2
    assert trace[0].name == "parent_span"
    
    all_traces = tracer.get_all_traces()
    print(f"Total {len(all_traces)} traces recorded")
    print("✓ 分布式追踪测试通过")
    return True


def test_stage83_alerts():
    """阶段83：告警系统测试"""
    print("\n=== 阶段83：告警系统 ===")
    alert_mgr = AlertManager()
    
    alert_mgr.add_rule({"name": "high_memory", "threshold": 90})
    alert = alert_mgr.create_alert(
        "test_alert", AlertSeverity.WARNING,
        "This is a test warning", {"value": 100}
    )
    
    print(f"Created alert: {alert.name} ({alert.severity.value})")
    active = alert_mgr.get_active_alerts()
    assert len(active) == 1
    
    resolved = alert_mgr.resolve_alert(alert.alert_id)
    assert resolved
    active = alert_mgr.get_active_alerts()
    assert len(active) == 0
    
    history = alert_mgr.get_alert_history()
    print(f"Alert history has {len(history)} entries")
    print("✓ 告警系统测试通过")
    return True


def test_stage85_log_analysis():
    """阶段85：日志分析测试"""
    print("\n=== 阶段85：日志分析 ===")
    analyzer = LogAnalyzer()
    
    analyzer.log(LogLevel.INFO, "Test info message", "test_module")
    analyzer.log(LogLevel.WARNING, "Test warning", "test_module")
    analyzer.log(LogLevel.ERROR, "Test error", "error_module")
    
    logs = analyzer.search_logs(limit=10)
    print(f"Logged {len(logs)} messages")
    assert len(logs) == 3
    
    errors = analyzer.search_logs(level=LogLevel.ERROR)
    print(f"Found {len(errors)} error logs")
    assert len(errors) == 1
    
    stats = analyzer.get_log_stats()
    print(f"Log stats: {stats}")
    print("✓ 日志分析测试通过")
    return True


def test_stage86_profiler():
    """阶段86：性能剖析测试"""
    print("\n=== 阶段86：性能剖析 ===")
    profiler = Profiler()
    
    @profiler.profile("test_function")
    def test_func():
        time.sleep(0.01)
        return "test"
    
    for _ in range(10):
        test_func()
    
    report = profiler.get_profile_report()
    print(f"Profile report has {len(report)} entries")
    assert "test_function" in report
    
    hotspots = profiler.find_hotspots()
    print(f"Found {len(hotspots)} hotspots")
    print("✓ 性能剖析测试通过")
    return True


def test_stage87_audit_log():
    """阶段87：审计日志测试"""
    print("\n=== 阶段87：审计日志 ===")
    auditor = AuditLogger()
    
    auditor.log_action("node_add", "user1", {"node": "test_node"})
    auditor.log_action("edge_add", "user2", {"from": "a", "to": "b"})
    auditor.log_action("node_add", "user1", {"node": "another_node"})
    
    logs = auditor.get_audit_log()
    print(f"Audit log has {len(logs)} entries")
    assert len(logs) == 3
    
    stats = auditor.get_action_stats()
    print(f"Action stats: {stats}")
    assert stats["node_add"] == 2
    print("✓ 审计日志测试通过")
    return True


def test_stage88_health_report():
    """阶段88：健康报告测试"""
    print("\n=== 阶段88：健康报告 ===")
    reporter = HealthReporter()
    
    def check1():
        return {"healthy": True, "message": "OK"}
    
    def check2():
        return {"healthy": False, "message": "Something wrong"}
    
    reporter.add_check(check1, "component1")
    reporter.add_check(check2, "component2")
    
    report = reporter.run_health_check()
    print(f"Health status: {report.status}, score: {report.score}")
    assert report.score == 80.0
    assert len(report.issues) == 1
    
    history = reporter.get_reports()
    print(f"Have {len(history)} reports")
    print("✓ 健康报告测试通过")
    return True


def test_stage90_observability_integration():
    """阶段90：可观测性集成测试"""
    print("\n=== 阶段90：可观测性集成 ===")
    system = ObservableSystem()
    
    # Generate some test data
    system.metrics.counter_add("test_count")
    system.tracer.start_span("test_span")
    system.alerts.create_alert("test_alert", AlertSeverity.INFO, "test")
    system.logs.log(LogLevel.INFO, "system log", "core")
    system.audit.log_action("test_action", "system")
    
    overview = system.get_overview()
    print(f"Observability overview: {overview}")
    
    export = system.export_all()
    print(f"Export contains {len(export.keys())} sections")
    print("✓ 可观测性集成测试通过")
    return True


def main():
    """阶段81-90综合测试"""
    print("=" * 60)
    print("阶段81-90：监控与可观测性综合测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_stage81_metrics()
    except Exception as e:
        print(f"✗ 阶段81测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage82_tracing()
    except Exception as e:
        print(f"✗ 阶段82测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage83_alerts()
    except Exception as e:
        print(f"✗ 阶段83测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage85_log_analysis()
    except Exception as e:
        print(f"✗ 阶段85测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage86_profiler()
    except Exception as e:
        print(f"✗ 阶段86测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage87_audit_log()
    except Exception as e:
        print(f"✗ 阶段87测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage88_health_report()
    except Exception as e:
        print(f"✗ 阶段88测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage90_observability_integration()
    except Exception as e:
        print(f"✗ 阶段90测试失败: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 阶段81-90所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    main()
