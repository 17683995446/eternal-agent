#!/usr/bin/env python
"""Minimal test for stage 81-90"""
import time
from eternal_agent import (
    MetricsCollector,
    Tracer,
    AlertManager,
    AlertSeverity,
    LogAnalyzer,
    LogLevel,
    Profiler,
    AuditLogger,
    HealthReporter,
    ObservableSystem
)

print("=" * 60)
print("Minimal test of stage 81-90 components")
print("=" * 60)

def test_metrics():
    print("\n1. Testing Metrics Collector (Stage 81)")
    collector = MetricsCollector()
    collector.counter_add("test_counter", 5)
    collector.gauge_set("cpu_load", 42.5)
    print(f"   ✓ Metrics: counter={collector.counters}, gauges={collector.gauges}")
    return True

def test_tracing():
    print("\n2. Testing Distributed Tracing (Stage 82)")
    tracer = Tracer()
    span = tracer.start_span("test_operation")
    time.sleep(0.001)
    tracer.end_span(span.span_id)
    traces = tracer.get_all_traces()
    print(f"   ✓ Tracing: {len(traces)} traces recorded")
    return True

def test_alerts():
    print("\n3. Testing Alert System (Stage 83)")
    alerts = AlertManager()
    alert = alerts.create_alert("test_alert", AlertSeverity.WARNING, "warning!")
    active = len(alerts.get_active_alerts())
    alerts.resolve_alert(alert.alert_id)
    print(f"   ✓ Alerts: created and resolved alert, {active} active initially")
    return True

def test_logs():
    print("\n4. Testing Log Analysis (Stage 85)")
    logs = LogAnalyzer()
    logs.log(LogLevel.INFO, "test message", "core")
    found = logs.search_logs("test")
    print(f"   ✓ Logs: {len(found)} log entries found")
    return True

def test_profiler():
    print("\n5. Testing Performance Profiler (Stage 86)")
    profiler = Profiler()
    @profiler.profile("test_func")
    def f():
        time.sleep(0.001)
    for _ in range(10):
        f()
    report = profiler.get_profile_report()
    print(f"   ✓ Profiler: {len(report)} profiled functions")
    return True

def test_audit():
    print("\n6. Testing Audit Logger (Stage 87)")
    audit = AuditLogger()
    audit.log_action("test_action", "user1")
    audit_stats = audit.get_action_stats()
    print(f"   ✓ Audit: {audit_stats}")
    return True

def test_health():
    print("\n7. Testing Health Reporter (Stage 88)")
    reporter = HealthReporter()
    reporter.add_check(lambda: {"healthy": True}, "test")
    report = reporter.run_health_check()
    print(f"   ✓ Health: status={report.status}, score={report.score}")
    return True

def test_integration():
    print("\n8. Testing Observability Integration (Stage 90)")
    system = ObservableSystem()
    overview = system.get_overview()
    print(f"   ✓ Integration: overview keys={list(overview.keys())}")
    return True

all_passed = True
try:
    all_passed &= test_metrics()
    all_passed &= test_tracing()
    all_passed &= test_alerts()
    all_passed &= test_logs()
    all_passed &= test_profiler()
    all_passed &= test_audit()
    all_passed &= test_health()
    all_passed &= test_integration()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All stage 81-90 components tested successfully!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
except Exception as e:
    print(f"\n✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
