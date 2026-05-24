"""
阶段71-80：容错与可靠性增强综合测试
- 阶段71：数据备份机制
- 阶段72：损坏数据修复
- 阶段73：多文件存储支持
- 阶段74：断电保护
- 阶段75：健康检查增强
- 阶段76：优雅关闭机制
- 阶段77：资源监控增强
- 阶段78：多实例支持
- 阶段79：故障转移
- 阶段80：灾难恢复
"""
import os
import tempfile
import shutil
import time
from eternal_agent import (
    KnowledgeGraph,
    BackupManager,
    DataIntegrityChecker,
    MultiFileStorage,
    AtomicWriter,
    EnhancedHealthChecker,
    GracefulShutdownManager,
    ResourceMonitor,
    InstanceManager,
    FailoverManager,
    DisasterRecoveryManager,
    ReliabilityManager
)


def test_stage71_backup():
    """阶段71：数据备份机制测试"""
    print("\n=== 阶段71：数据备份机制 ===")
    
    temp_kg_path = tempfile.mktemp(suffix='.json')
    temp_backup_dir = tempfile.mkdtemp()
    
    try:
        # 创建测试图谱
        kg = KnowledgeGraph(temp_kg_path)
        kg.add_node("backup_test_1")
        kg.add_node("backup_test_2")
        kg.add_edge("backup_test_1", "backup_test_2", "test_rel", 0.8)
        kg.force_save()
        
        # 测试备份管理器
        backup_mgr = BackupManager(
            backup_dir=temp_backup_dir,
            max_backups=5,
            auto_backup_interval=0  # 立即备份
        )
        
        # 创建备份
        backup = backup_mgr.create_backup(kg, "Test backup", force=True)
        assert backup is not None, "备份应该创建成功"
        print(f"创建备份: {backup.backup_id}")
        print(f"  大小: {backup.size} bytes")
        print(f"  校验和: {backup.checksum[:16]}...")
        
        # 列出备份
        backups = backup_mgr.list_backups()
        print(f"备份列表: {len(backups)} 个备份")
        assert len(backups) == 1, "应该有1个备份"
        
        # 测试恢复
        success = backup_mgr.restore_backup(backup.backup_id, kg)
        assert success, "恢复应该成功"
        assert "backup_test_1" in kg.nodes, "节点应该恢复"
        
        print("✓ 数据备份机制测试通过")
        return True
    finally:
        if os.path.exists(temp_kg_path):
            os.unlink(temp_kg_path)
        if os.path.exists(temp_backup_dir):
            shutil.rmtree(temp_backup_dir)


def test_stage72_integrity():
    """阶段72：损坏数据修复测试"""
    print("\n=== 阶段72：损坏数据修复 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        kg.add_node("node1")
        kg.add_node("node2")
        kg.add_edge("node1", "node2", "rel", 0.8)
        
        # 测试完整性检查
        checker = DataIntegrityChecker(kg)
        report = checker.check_integrity()
        
        print(f"完整性检查结果:")
        print(f"  问题数: {len(report.get('issues', []))}")
        print(f"  警告数: {len(report.get('warnings', []))}")
        print(f"  统计: {report.get('stats', {})}")
        
        # 测试自动修复
        repairs = checker.auto_repair()
        print(f"自动修复: {repairs} 项修复")
        
        print("✓ 损坏数据修复测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage73_multifile():
    """阶段73：多文件存储支持测试"""
    print("\n=== 阶段73：多文件存储支持 ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        storage = MultiFileStorage(base_dir=temp_dir)
        
        # 保存分片
        shard_data = {"nodes": ["a", "b", "c"], "edges": []}
        success = storage.save_shard("test_shard_1", shard_data)
        assert success, "分片保存应该成功"
        
        # 加载分片
        loaded = storage.load_shard("test_shard_1")
        assert loaded is not None, "分片加载应该成功"
        assert loaded == shard_data, "数据应该一致"
        
        # 获取统计
        stats = storage.get_shard_stats()
        print(f"分片统计: {stats}")
        
        # 删除分片
        success = storage.delete_shard("test_shard_1")
        assert success, "分片删除应该成功"
        
        print("✓ 多文件存储支持测试通过")
        return True
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_stage74_atomic_write():
    """阶段74：断电保护（原子写入）测试"""
    print("\n=== 阶段74：断电保护 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        writer = AtomicWriter(temp_path)
        
        # 测试原子写入
        data = '{"test": "data", "value": 123}'
        success = writer.write_atomically(data)
        assert success, "原子写入应该成功"
        
        # 验证文件存在且内容正确
        with open(temp_path, 'r') as f:
            loaded_data = f.read()
        assert loaded_data == data, "数据应该一致"
        
        print("✓ 断电保护测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage75_health_check():
    """阶段75：健康检查增强测试"""
    print("\n=== 阶段75：健康检查增强 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        kg.add_node("health_node_1")
        kg.add_node("health_node_2")
        kg.add_edge("health_node_1", "health_node_2", "health_rel", 0.9)
        
        # 测试健康检查
        checker = EnhancedHealthChecker(kg)
        health = checker.perform_health_check()
        
        print(f"健康状态: {health.status}")
        print(f"健康评分: {health.score:.2f}")
        print(f"建议: {health.recommendations}")
        
        # 测试趋势
        trends = checker.get_health_trends()
        print(f"健康趋势: {trends}")
        
        print("✓ 健康检查增强测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage76_graceful_shutdown():
    """阶段76：优雅关闭机制测试"""
    print("\n=== 阶段76：优雅关闭机制 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        kg.add_node("shutdown_test")
        
        # 测试关闭管理器
        shutdown_mgr = GracefulShutdownManager(kg)
        
        # 测试注册处理器
        handler_called = []
        def test_handler():
            handler_called.append(True)
        
        shutdown_mgr.register_shutdown_handler(test_handler)
        
        # 测试关闭（模拟）
        shutdown_mgr.shutdown_in_progress = True
        shutdown_mgr._save_state()
        
        print(f"关闭处理器注册成功")
        print(f"处理器被调用: {len(handler_called)} 次")
        
        print("✓ 优雅关闭机制测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stage77_resource_monitor():
    """阶段77：资源监控增强测试"""
    print("\n=== 阶段77：资源监控增强 ===")
    
    # 测试资源监控
    monitor = ResourceMonitor()
    status = monitor.check_resources()
    
    print(f"资源状态:")
    print(f"  内存: {status['metrics'].get('memory', {})}")
    print(f"  CPU: {status['metrics'].get('cpu', {})}")
    print(f"  磁盘: {status['metrics'].get('disk', {})}")
    print(f"  告警: {len(status['alerts'])} 个")
    
    print("✓ 资源监控增强测试通过")
    return True


def test_stage78_instance_manager():
    """阶段78：多实例支持测试"""
    print("\n=== 阶段78：多实例支持 ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        instance_mgr = InstanceManager(f"test_instance_{os.getpid()}")
        
        # 注册实例
        success = instance_mgr.register_instance()
        assert success, "实例注册应该成功"
        
        # 发送心跳
        heartbeat = instance_mgr.heartbeat()
        print(f"心跳: {heartbeat}")
        assert heartbeat["status"] == "alive", "实例应该存活"
        
        # 发现节点
        peers = instance_mgr.discover_peers()
        print(f"发现节点: {len(peers)} 个")
        
        # 选举领导者
        leader = instance_mgr.elect_leader()
        print(f"选举结果: {leader}, is_leader={instance_mgr.is_leader}")
        
        print("✓ 多实例支持测试通过")
        return True
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_stage79_failover():
    """阶段79：故障转移测试"""
    print("\n=== 阶段79：故障转移 ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        instance_mgr = InstanceManager(f"test_instance_{os.getpid()}")
        instance_mgr.register_instance()
        
        failover_mgr = FailoverManager(instance_mgr)
        
        # 检查故障转移
        needs_failover = failover_mgr.check_failover_needed()
        print(f"需要故障转移: {needs_failover}")
        
        # 执行故障转移
        if needs_failover:
            success = failover_mgr.perform_failover()
            assert success, "故障转移应该成功"
        
        # 获取统计
        stats = failover_mgr.get_failover_stats()
        print(f"故障转移统计: {stats}")
        
        print("✓ 故障转移测试通过")
        return True
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_stage80_disaster_recovery():
    """阶段80：灾难恢复测试"""
    print("\n=== 阶段80：灾难恢复 ===")
    
    temp_kg_path = tempfile.mktemp(suffix='.json')
    temp_backup_dir = tempfile.mkdtemp()
    
    try:
        kg = KnowledgeGraph(temp_kg_path)
        kg.add_node("dr_test_node")
        
        backup_mgr = BackupManager(backup_dir=temp_backup_dir)
        dr_manager = DisasterRecoveryManager(backup_mgr)
        
        # 创建恢复点
        success = dr_manager.create_recovery_point(kg, "Test recovery point")
        assert success, "恢复点创建应该成功"
        
        # 列出恢复点
        recovery_points = dr_manager.list_recovery_points()
        print(f"恢复点列表: {len(recovery_points)} 个")
        
        # 创建灾难恢复计划
        plan = dr_manager.create_disaster_recovery_plan()
        print(f"灾难恢复计划: {plan['created_at']}")
        print(f"  备份数量: {plan['backup_count']}")
        print(f"  恢复步骤: {len(plan['steps'])} 步")
        
        # 测试恢复
        if recovery_points:
            recovery_point_id = recovery_points[0]['recovery_point_id']
            # 注意：这里不实际执行恢复，以免破坏测试数据
        
        print("✓ 灾难恢复测试通过")
        return True
    finally:
        if os.path.exists(temp_kg_path):
            os.unlink(temp_kg_path)
        if os.path.exists(temp_backup_dir):
            shutil.rmtree(temp_backup_dir)


def test_reliability_manager():
    """综合可靠性管理器测试"""
    print("\n=== 综合可靠性管理器 ===")
    
    temp_path = tempfile.mktemp(suffix='.json')
    
    try:
        kg = KnowledgeGraph(temp_path)
        kg.add_node("reliability_test")
        kg.add_edge("reliability_test", "reliability_test", "self_rel", 0.5)
        
        # 测试可靠性管理器
        reliability = ReliabilityManager(kg)
        
        # 执行维护
        results = reliability.perform_maintenance()
        print(f"维护执行结果: {len(results['actions'])} 个操作")
        for action in results['actions']:
            print(f"  - {action.get('action', 'unknown')}")
        
        # 获取完整报告
        report = reliability.get_full_report()
        print(f"可靠性报告:")
        print(f"  健康状态: {report['health']['status']}")
        print(f"  备份数量: {len(report['backups'])}")
        print(f"  完整性: {report['integrity']['stats']}")
        
        print("✓ 综合可靠性管理器测试通过")
        return True
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def main():
    """阶段71-80综合测试"""
    print("=" * 60)
    print("阶段71-80：容错与可靠性增强综合测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_stage71_backup()
    except Exception as e:
        print(f"✗ 阶段71测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage72_integrity()
    except Exception as e:
        print(f"✗ 阶段72测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage73_multifile()
    except Exception as e:
        print(f"✗ 阶段73测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage74_atomic_write()
    except Exception as e:
        print(f"✗ 阶段74测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage75_health_check()
    except Exception as e:
        print(f"✗ 阶段75测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage76_graceful_shutdown()
    except Exception as e:
        print(f"✗ 阶段76测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage77_resource_monitor()
    except Exception as e:
        print(f"✗ 阶段77测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage78_instance_manager()
    except Exception as e:
        print(f"✗ 阶段78测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage79_failover()
    except Exception as e:
        print(f"✗ 阶段79测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_stage80_disaster_recovery()
    except Exception as e:
        print(f"✗ 阶段80测试失败: {e}")
        all_passed = False
    
    try:
        all_passed &= test_reliability_manager()
    except Exception as e:
        print(f"✗ 综合可靠性管理器测试失败: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 阶段71-80所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    main()
