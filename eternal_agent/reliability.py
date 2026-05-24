"""
基于第一性原理的轻量永动知识图谱 Agent
阶段71-80：容错与可靠性增强
"""

import os
import shutil
import json
import hashlib
import signal
import atexit
import psutil
import time
import tempfile
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Lock
from .knowledge_graph import KnowledgeGraph
from .utils import logger, get_timestamp

# ========================================
# 阶段71：数据备份机制
# ========================================

@dataclass
class BackupMetadata:
    """备份元数据"""
    backup_id: str
    timestamp: float
    file_path: str
    checksum: str
    size: int
    graph_stats: Dict[str, int]
    description: str = ""

class BackupManager:
    """备份管理器 - 阶段71"""
    
    def __init__(
        self,
        backup_dir: str = "backups",
        max_backups: int = 10,
        auto_backup_interval: int = 3600
    ):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = max_backups
        self.auto_backup_interval = auto_backup_interval
        self.last_backup_time = 0
        self.backup_lock = Lock()
        self._backups: List[BackupMetadata] = []
        self._load_backup_metadata()
    
    def _load_backup_metadata(self):
        """加载备份元数据"""
        metadata_file = self.backup_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    self._backups = [BackupMetadata(**b) for b in data.get('backups', [])]
            except Exception as e:
                logger.warning(f"Failed to load backup metadata: {e}")
    
    def _save_backup_metadata(self):
        """保存备份元数据"""
        metadata_file = self.backup_dir / "metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump({
                    'backups': [asdict(b) for b in self._backups]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    def _compute_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def create_backup(
        self,
        kg: KnowledgeGraph,
        description: str = "",
        force: bool = False
    ) -> Optional[BackupMetadata]:
        """
        创建备份
        """
        with self.backup_lock:
            # 检查是否需要备份
            current_time = time.time()
            if not force and (current_time - self.last_backup_time) < self.auto_backup_interval:
                logger.debug("Backup interval not reached, skipping")
                return None
            
            # 强制保存当前图谱
            kg.force_save()
            
            # 创建备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp}"
            backup_path = self.backup_dir / f"{backup_id}.json"
            
            try:
                # 复制文件
                shutil.copy2(kg.save_path, backup_path)
                
                # 计算校验和
                checksum = self._compute_checksum(str(backup_path))
                
                # 创建元数据
                stats = kg.get_stats()
                metadata = BackupMetadata(
                    backup_id=backup_id,
                    timestamp=current_time,
                    file_path=str(backup_path),
                    checksum=checksum,
                    size=os.path.getsize(backup_path),
                    graph_stats=stats,
                    description=description
                )
                
                # 添加到列表
                self._backups.append(metadata)
                self.last_backup_time = current_time
                
                # 清理旧备份
                self._cleanup_old_backups()
                
                # 保存元数据
                self._save_backup_metadata()
                
                logger.info(f"Created backup: {backup_id}, size: {metadata.size} bytes")
                return metadata
                
            except Exception as e:
                logger.error(f"Failed to create backup: {e}")
                return None
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        if len(self._backups) <= self.max_backups:
            return
        
        # 按时间排序，保留最新的
        self._backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 删除多余的
        for backup in self._backups[self.max_backups:]:
            try:
                if os.path.exists(backup.file_path):
                    os.unlink(backup.file_path)
                logger.info(f"Deleted old backup: {backup.backup_id}")
            except Exception as e:
                logger.error(f"Failed to delete backup {backup.backup_id}: {e}")
        
        self._backups = self._backups[:self.max_backups]
    
    def list_backups(self) -> List[BackupMetadata]:
        """列出所有备份"""
        return sorted(self._backups, key=lambda x: x.timestamp, reverse=True)
    
    def restore_backup(
        self,
        backup_id: str,
        kg: KnowledgeGraph
    ) -> bool:
        """恢复备份"""
        backup = None
        for b in self._backups:
            if b.backup_id == backup_id:
                backup = b
                break
        
        if not backup:
            logger.error(f"Backup not found: {backup_id}")
            return False
        
        if not os.path.exists(backup.file_path):
            logger.error(f"Backup file not found: {backup.file_path}")
            return False
        
        # 验证校验和
        current_checksum = self._compute_checksum(backup.file_path)
        if current_checksum != backup.checksum:
            logger.error(f"Backup checksum mismatch! Expected {backup.checksum}, got {current_checksum}")
            return False
        
        try:
            # 创建当前数据的备份
            self.create_backup(kg, "Auto-backup before restore", force=True)
            
            # 恢复文件
            shutil.copy2(backup.file_path, kg.save_path)
            
            # 重新加载
            kg.load()
            
            logger.info(f"Successfully restored backup: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        with self.backup_lock:
            for i, backup in enumerate(self._backups):
                if backup.backup_id == backup_id:
                    try:
                        if os.path.exists(backup.file_path):
                            os.unlink(backup.file_path)
                        del self._backups[i]
                        self._save_backup_metadata()
                        logger.info(f"Deleted backup: {backup_id}")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to delete backup: {e}")
                        return False
            return False

# ========================================
# 阶段72：损坏数据修复
# ========================================

class DataIntegrityChecker:
    """数据完整性检查器 - 阶段72"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.integrity_report: Dict[str, Any] = {}
    
    def check_integrity(self) -> Dict[str, Any]:
        """
        检查数据完整性
        """
        report = {
            "timestamp": get_timestamp(),
            "issues": [],
            "warnings": [],
            "stats": {}
        }
        
        # 检查节点完整性
        for name, node in self.kg.nodes.items():
            if not isinstance(name, str) or not name:
                report["issues"].append(f"Invalid node name: {name}")
            
            if not hasattr(node, 'created_at'):
                report["issues"].append(f"Node {name} missing created_at")
            
            if not hasattr(node, 'is_valid'):
                report["warnings"].append(f"Node {name} missing is_valid field")
        
        # 检查边完整性
        seen_edges = set()
        for edge in self.kg.edges:
            # 检查源和目标
            if edge.source not in self.kg.nodes:
                report["issues"].append(f"Edge references non-existent source: {edge.source}")
            
            if edge.target not in self.kg.nodes:
                report["issues"].append(f"Edge references non-existent target: {edge.target}")
            
            # 检查重复边
            edge_key = (edge.source, edge.target, edge.relation_name)
            if edge_key in seen_edges:
                report["warnings"].append(f"Duplicate edge: {edge_key}")
            seen_edges.add(edge_key)
            
            # 检查权重
            if not hasattr(edge, 'weight') or not (0 <= edge.weight <= 1):
                report["warnings"].append(f"Edge {edge_key} has invalid weight")
        
        # 检查孤立节点
        connected_nodes = set()
        for edge in self.kg.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        isolated = set(self.kg.nodes.keys()) - connected_nodes
        if isolated:
            report["warnings"].append(f"Found {len(isolated)} isolated nodes")
        
        report["stats"] = {
            "total_nodes": len(self.kg.nodes),
            "total_edges": len(self.kg.edges),
            "isolated_nodes": len(isolated),
            "issues_count": len(report["issues"]),
            "warnings_count": len(report["warnings"])
        }
        
        self.integrity_report = report
        return report
    
    def auto_repair(self) -> int:
        """
        自动修复问题
        """
        repairs = 0
        report = self.check_integrity()
        
        # 修复问题
        for issue in report["issues"]:
            if "Edge references non-existent source" in issue:
                # 删除引用不存在节点的边
                source = issue.split(": ")[1]
                edges_to_remove = [
                    e for e in self.kg.edges
                    if e.source == source
                ]
                for edge in edges_to_remove:
                    self.kg.remove_edge(edge.source, edge.target)
                    repairs += 1
                    logger.info(f"Removed edge with invalid source: {edge.source}->{edge.target}")
            
            elif "Edge references non-existent target" in issue:
                target = issue.split(": ")[1]
                edges_to_remove = [
                    e for e in self.kg.edges
                    if e.target == target
                ]
                for edge in edges_to_remove:
                    self.kg.remove_edge(edge.source, edge.target)
                    repairs += 1
                    logger.info(f"Removed edge with invalid target: {edge.source}->{edge.target}")
        
        # 重新保存
        if repairs > 0:
            self.kg.force_save()
        
        logger.info(f"Auto-repair completed: {repairs} repairs made")
        return repairs

# ========================================
# 阶段73：多文件存储支持
# ========================================

class MultiFileStorage:
    """多文件存储管理器 - 阶段73"""
    
    def __init__(
        self,
        base_dir: str = "data",
        shard_size: int = 1000,
        max_shards: int = 100
    ):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.shard_size = shard_size
        self.max_shards = max_shards
        self.shard_index: Dict[str, str] = {}  # node_name -> shard_file
        self._load_shard_index()
    
    def _load_shard_index(self):
        """加载分片索引"""
        index_file = self.base_dir / "shard_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.shard_index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load shard index: {e}")
    
    def _save_shard_index(self):
        """保存分片索引"""
        index_file = self.base_dir / "shard_index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump(self.shard_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save shard index: {e}")
    
    def save_shard(
        self,
        shard_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """保存分片"""
        shard_file = self.base_dir / f"shard_{shard_id}.json"
        try:
            with open(shard_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"Saved shard: {shard_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save shard {shard_id}: {e}")
            return False
    
    def load_shard(self, shard_id: str) -> Optional[Dict[str, Any]]:
        """加载分片"""
        shard_file = self.base_dir / f"shard_{shard_id}.json"
        if not shard_file.exists():
            return None
        
        try:
            with open(shard_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load shard {shard_id}: {e}")
            return None
    
    def delete_shard(self, shard_id: str) -> bool:
        """删除分片"""
        shard_file = self.base_dir / f"shard_{shard_id}.json"
        try:
            if shard_file.exists():
                shard_file.unlink()
                logger.info(f"Deleted shard: {shard_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete shard {shard_id}: {e}")
            return False
    
    def get_shard_stats(self) -> Dict[str, Any]:
        """获取分片统计"""
        shards = list(self.base_dir.glob("shard_*.json"))
        total_size = sum(f.stat().st_size for f in shards)
        
        return {
            "shard_count": len(shards),
            "total_size": total_size,
            "indexed_nodes": len(self.shard_index)
        }

# ========================================
# 阶段74：断电保护（原子写入）
# ========================================

class AtomicWriter:
    """原子写入器 - 阶段74"""
    
    def __init__(self, target_file: str):
        self.target_file = Path(target_file)
        self.temp_file = None
    
    def write_atomically(self, data: str) -> bool:
        """
        原子写入数据
        使用写时复制技术防止断电损坏
        """
        try:
            # 创建临时文件
            fd, self.temp_file = tempfile.mkstemp(
                dir=self.target_file.parent,
                prefix='.tmp_',
                suffix='.json'
            )
            
            # 写入临时文件
            with os.fdopen(fd, 'w') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())  # 确保写入磁盘
            
            # 原子替换
            os.replace(self.temp_file, self.target_file)
            self.temp_file = None
            
            logger.debug(f"Atomic write completed: {self.target_file}")
            return True
            
        except Exception as e:
            logger.error(f"Atomic write failed: {e}")
            # 清理临时文件
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.unlink(self.temp_file)
                except:
                    pass
            return False
    
    def emergency_cleanup(self):
        """紧急清理临时文件"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.unlink(self.temp_file)
                logger.info("Cleaned up temporary file")
            except Exception as e:
                logger.error(f"Failed to cleanup temp file: {e}")

# ========================================
# 阶段75：健康检查增强
# ========================================

@dataclass
class HealthStatus:
    """健康状态"""
    status: str  # healthy, degraded, unhealthy
    timestamp: float
    checks: Dict[str, Any]
    score: float  # 0-1
    recommendations: List[str]

class EnhancedHealthChecker:
    """增强的健康检查器 - 阶段75"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.health_history: deque = deque(maxlen=100)
    
    def perform_health_check(self) -> HealthStatus:
        """
        执行深度健康检查
        """
        checks = {}
        recommendations = []
        score = 1.0
        
        # 1. 数据完整性检查
        integrity = DataIntegrityChecker(self.kg).check_integrity()
        checks["data_integrity"] = integrity
        issues_count = integrity.get("stats", {}).get("issues_count", 0)
        if issues_count > 0:
            score -= 0.3
            recommendations.append(f"Fix {issues_count} data integrity issues")
        
        # 2. 资源使用检查
        resource_check = self._check_resources()
        checks["resources"] = resource_check
        if resource_check.get("memory_percent", 0) > 80:
            score -= 0.2
            recommendations.append("High memory usage detected")
        
        # 3. 磁盘空间检查
        disk_check = self._check_disk_space()
        checks["disk_space"] = disk_check
        if disk_check.get("percent_used", 0) > 90:
            score -= 0.2
            recommendations.append("Low disk space, consider cleanup")
        
        # 4. 图谱健康检查
        graph_health = self._check_graph_health()
        checks["graph_health"] = graph_health
        if graph_health.get("isolated_nodes_percent", 0) > 50:
            score -= 0.1
            recommendations.append("High percentage of isolated nodes")
        
        # 5. 性能检查
        performance = self._check_performance()
        checks["performance"] = performance
        if performance.get("avg_degree", 0) > 100:
            score -= 0.1
            recommendations.append("Graph has high average degree, consider optimization")
        
        # 确定状态
        if score >= 0.8:
            status = "healthy"
        elif score >= 0.5:
            status = "degraded"
        else:
            status = "unhealthy"
        
        health_status = HealthStatus(
            status=status,
            timestamp=get_timestamp(),
            checks=checks,
            score=max(0.0, score),
            recommendations=recommendations
        )
        
        # 保存历史
        self.health_history.append(health_status)
        
        return health_status
    
    def _check_resources(self) -> Dict[str, Any]:
        """检查资源使用"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "memory_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "num_threads": process.num_threads()
            }
        except Exception as e:
            logger.warning(f"Failed to check resources: {e}")
            return {}
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            path = self.kg.save_path if hasattr(self.kg, 'save_path') else '.'
            usage = psutil.disk_usage(path)
            
            return {
                "total_gb": usage.total / 1024 / 1024 / 1024,
                "used_gb": usage.used / 1024 / 1024 / 1024,
                "free_gb": usage.free / 1024 / 1024 / 1024,
                "percent_used": usage.percent
            }
        except Exception as e:
            logger.warning(f"Failed to check disk space: {e}")
            return {}
    
    def _check_graph_health(self) -> Dict[str, Any]:
        """检查图谱健康"""
        connected_nodes = set()
        for edge in self.kg.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        isolated_count = len(self.kg.nodes) - len(connected_nodes)
        total_nodes = len(self.kg.nodes) if self.kg.nodes else 1
        
        return {
            "total_nodes": len(self.kg.nodes),
            "total_edges": len(self.kg.edges),
            "isolated_nodes": isolated_count,
            "isolated_nodes_percent": (isolated_count / total_nodes) * 100,
            "avg_degree": (len(self.kg.edges) * 2 / total_nodes) if total_nodes > 0 else 0
        }
    
    def _check_performance(self) -> Dict[str, Any]:
        """检查性能指标"""
        return {
            "avg_degree": self._calculate_avg_degree(),
            "graph_density": self._calculate_density()
        }
    
    def _calculate_avg_degree(self) -> float:
        """计算平均度数"""
        if not self.kg.nodes:
            return 0.0
        
        total_degree = sum(len(self.kg.get_neighbors(n)) for n in self.kg.nodes)
        return total_degree / len(self.kg.nodes)
    
    def _calculate_density(self) -> float:
        """计算图密度"""
        n = len(self.kg.nodes)
        if n < 2:
            return 0.0
        
        max_edges = n * (n - 1) / 2
        return len(self.kg.edges) / max_edges if max_edges > 0 else 0.0
    
    def get_health_trends(self) -> Dict[str, Any]:
        """获取健康趋势"""
        if len(self.health_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent = list(self.health_history)[-10:]
        avg_score = sum(h.score for h in recent) / len(recent)
        
        return {
            "recent_scores": [h.score for h in recent],
            "average_score": avg_score,
            "status_distribution": self._count_statuses()
        }
    
    def _count_statuses(self) -> Dict[str, int]:
        """统计状态分布"""
        counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}
        for h in self.health_history:
            counts[h.status] += 1
        return counts

# ========================================
# 阶段76：优雅关闭机制
# ========================================

class GracefulShutdownManager:
    """优雅关闭管理器 - 阶段76"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.shutdown_in_progress = False
        self.shutdown_handlers: List[callable] = []
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """注册信号处理器"""
        try:
            signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
            signal.signal(signal.SIGINT, self._handle_shutdown_signal)
            atexit.register(self._cleanup)
            logger.info("Registered shutdown signal handlers")
        except Exception as e:
            logger.warning(f"Failed to register signal handlers: {e}")
    
    def _handle_shutdown_signal(self, signum, frame):
        """处理关闭信号"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received shutdown signal: {signal_name}")
        self.initiate_graceful_shutdown()
    
    def _cleanup(self):
        """清理函数"""
        if not self.shutdown_in_progress:
            logger.info("Performing cleanup...")
            self._save_state()
    
    def register_shutdown_handler(self, handler: callable):
        """注册关闭处理器"""
        self.shutdown_handlers.append(handler)
    
    def initiate_graceful_shutdown(self, timeout: int = 30):
        """
        发起优雅关闭
        """
        if self.shutdown_in_progress:
            logger.warning("Shutdown already in progress")
            return
        
        self.shutdown_in_progress = True
        logger.info("Initiating graceful shutdown...")
        
        start_time = time.time()
        
        try:
            # 1. 保存状态
            logger.info("Step 1: Saving state...")
            self._save_state()
            
            # 2. 执行关闭处理器
            logger.info("Step 2: Executing shutdown handlers...")
            for handler in self.shutdown_handlers:
                try:
                    handler()
                except Exception as e:
                    logger.error(f"Shutdown handler failed: {e}")
            
            # 3. 等待完成
            elapsed = time.time() - start_time
            if elapsed < timeout:
                time.sleep(max(0, timeout - elapsed))
            
            logger.info("Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            self.shutdown_in_progress = False
    
    def _save_state(self):
        """保存状态"""
        try:
            if hasattr(self.kg, 'force_save'):
                self.kg.force_save()
            logger.info("State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

# ========================================
# 阶段77：资源监控增强
# ========================================

class ResourceMonitor:
    """资源监控器 - 阶段77"""
    
    def __init__(self, alert_threshold: Dict[str, float] = None):
        if alert_threshold is None:
            alert_threshold = {
                "memory_percent": 80.0,
                "cpu_percent": 90.0,
                "disk_percent": 85.0
            }
        self.alert_threshold = alert_threshold
        self.alerts: deque = deque(maxlen=100)
        self._last_alert_time: Dict[str, float] = {}
        self.alert_cooldown = 300  # 5分钟内不重复告警
    
    def check_resources(self) -> Dict[str, Any]:
        """检查资源并返回状态"""
        status = {
            "timestamp": get_timestamp(),
            "alerts": [],
            "metrics": {}
        }
        
        # 内存检查
        memory = self._check_memory()
        status["metrics"]["memory"] = memory
        if memory["percent"] > self.alert_threshold["memory_percent"]:
            self._create_alert("memory", f"Memory usage high: {memory['percent']:.1f}%")
        
        # CPU检查
        cpu = self._check_cpu()
        status["metrics"]["cpu"] = cpu
        if cpu["percent"] > self.alert_threshold["cpu_percent"]:
            self._create_alert("cpu", f"CPU usage high: {cpu['percent']:.1f}%")
        
        # 磁盘检查
        disk = self._check_disk()
        status["metrics"]["disk"] = disk
        if disk["percent"] > self.alert_threshold["disk_percent"]:
            self._create_alert("disk", f"Disk usage high: {disk['percent']:.1f}%")
        
        status["alerts"] = list(self.alerts)[-10:]
        return status
    
    def _check_memory(self) -> Dict[str, Any]:
        """检查内存"""
        try:
            vm = psutil.virtual_memory()
            return {
                "total_mb": vm.total / 1024 / 1024,
                "available_mb": vm.available / 1024 / 1024,
                "percent": vm.percent,
                "used_mb": vm.used / 1024 / 1024
            }
        except Exception as e:
            logger.warning(f"Failed to check memory: {e}")
            return {}
    
    def _check_cpu(self) -> Dict[str, Any]:
        """检查CPU"""
        try:
            return {
                "percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count(),
                "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True)
            }
        except Exception as e:
            logger.warning(f"Failed to check CPU: {e}")
            return {}
    
    def _check_disk(self) -> Dict[str, Any]:
        """检查磁盘"""
        try:
            usage = psutil.disk_usage('/')
            return {
                "total_gb": usage.total / 1024 / 1024 / 1024,
                "used_gb": usage.used / 1024 / 1024 / 1024,
                "free_gb": usage.free / 1024 / 1024 / 1024,
                "percent": usage.percent
            }
        except Exception as e:
            logger.warning(f"Failed to check disk: {e}")
            return {}
    
    def _create_alert(self, alert_type: str, message: str):
        """创建告警"""
        current_time = time.time()
        
        # 检查冷却期
        if alert_type in self._last_alert_time:
            if current_time - self._last_alert_time[alert_type] < self.alert_cooldown:
                return
        
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": current_time
        }
        
        self.alerts.append(alert)
        self._last_alert_time[alert_type] = current_time
        logger.warning(f"Alert: {message}")

# ========================================
# 阶段78：多实例支持
# ========================================

class InstanceManager:
    """实例管理器 - 阶段78"""
    
    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.instance_dir = Path(f"instances/{instance_id}")
        self.instance_dir.mkdir(parents=True, exist_ok=True)
        self.is_leader = False
        self.peers: Set[str] = set()
    
    def register_instance(self) -> bool:
        """注册实例"""
        try:
            # 创建实例标记文件
            marker_file = self.instance_dir / "instance.marker"
            with open(marker_file, 'w') as f:
                json.dump({
                    "instance_id": self.instance_id,
                    "start_time": get_timestamp(),
                    "hostname": os.uname().nodename
                }, f)
            
            logger.info(f"Instance {self.instance_id} registered")
            return True
        except Exception as e:
            logger.error(f"Failed to register instance: {e}")
            return False
    
    def heartbeat(self) -> Dict[str, Any]:
        """发送心跳"""
        heartbeat_file = self.instance_dir / "heartbeat"
        try:
            with open(heartbeat_file, 'w') as f:
                json.dump({
                    "instance_id": self.instance_id,
                    "timestamp": get_timestamp(),
                    "is_leader": self.is_leader
                }, f)
            
            return {
                "instance_id": self.instance_id,
                "timestamp": get_timestamp(),
                "status": "alive"
            }
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def discover_peers(self) -> Set[str]:
        """发现其他实例"""
        instances_base = Path("instances")
        if not instances_base.exists():
            return set()
        
        peers = set()
        for instance_dir in instances_base.iterdir():
            if instance_dir.is_dir() and instance_dir.name != self.instance_id:
                marker_file = instance_dir / "instance.marker"
                if marker_file.exists():
                    try:
                        with open(marker_file, 'r') as f:
                            data = json.load(f)
                            peers.add(data.get("instance_id", instance_dir.name))
                    except:
                        pass
        
        self.peers = peers
        return peers
    
    def elect_leader(self) -> Optional[str]:
        """选举领导者（简单策略：字典序最小）"""
        self.discover_peers()
        all_instances = self.peers | {self.instance_id}
        
        # 选择字典序最小的作为领导者
        leader = min(all_instances)
        self.is_leader = (leader == self.instance_id)
        
        logger.info(f"Leader elected: {leader}, is_leader={self.is_leader}")
        return leader if self.is_leader else None

# ========================================
# 阶段79：故障转移
# ========================================

class FailoverManager:
    """故障转移管理器 - 阶段79"""
    
    def __init__(self, instance_manager: InstanceManager):
        self.instance_manager = instance_manager
        self.failover_history: List[Dict] = []
        self.primary_instance: Optional[str] = None
    
    def check_failover_needed(self) -> bool:
        """检查是否需要故障转移"""
        peers = self.instance_manager.discover_peers()
        
        # 如果没有主实例，需要选举
        if not self.primary_instance:
            return True
        
        # 检查主实例是否还活着
        primary_dir = Path(f"instances/{self.primary_instance}")
        heartbeat_file = primary_dir / "heartbeat"
        
        if not heartbeat_file.exists():
            logger.warning(f"Primary instance {self.primary_instance} heartbeat not found")
            return True
        
        try:
            with open(heartbeat_file, 'r') as f:
                data = json.load(f)
                last_heartbeat = data.get("timestamp", 0)
                
                # 如果超过60秒没有心跳，认为已故障
                if get_timestamp() - last_heartbeat > 60:
                    logger.warning(f"Primary instance {self.primary_instance} seems down")
                    return True
        except Exception as e:
            logger.error(f"Failed to check primary heartbeat: {e}")
            return True
        
        return False
    
    def perform_failover(self) -> bool:
        """执行故障转移"""
        try:
            logger.info("Starting failover process...")
            
            # 记录历史
            record = {
                "timestamp": get_timestamp(),
                "old_primary": self.primary_instance,
                "new_primary": self.instance_manager.instance_id
            }
            self.failover_history.append(record)
            
            # 设置新的主实例
            self.primary_instance = self.instance_manager.instance_id
            self.instance_manager.is_leader = True
            
            logger.info(f"Failover completed: new primary is {self.primary_instance}")
            return True
            
        except Exception as e:
            logger.error(f"Failover failed: {e}")
            return False
    
    def get_failover_stats(self) -> Dict[str, Any]:
        """获取故障转移统计"""
        return {
            "total_failovers": len(self.failover_history),
            "last_failover": self.failover_history[-1] if self.failover_history else None,
            "current_primary": self.primary_instance
        }

# ========================================
# 阶段80：灾难恢复
# ========================================

class DisasterRecoveryManager:
    """灾难恢复管理器 - 阶段80"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.recovery_points: List[Dict] = []
    
    def create_recovery_point(self, kg: KnowledgeGraph, description: str = "") -> bool:
        """创建恢复点"""
        try:
            backup = self.backup_manager.create_backup(
                kg,
                description=f"Recovery point: {description}",
                force=True
            )
            
            if backup:
                self.recovery_points.append({
                    "recovery_point_id": backup.backup_id,
                    "timestamp": backup.timestamp,
                    "description": description,
                    "stats": backup.graph_stats
                })
                logger.info(f"Created recovery point: {backup.backup_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to create recovery point: {e}")
            return False
    
    def list_recovery_points(self) -> List[Dict]:
        """列出所有恢复点"""
        return sorted(self.recovery_points, key=lambda x: x["timestamp"], reverse=True)
    
    def restore_to_point(
        self,
        recovery_point_id: str,
        kg: KnowledgeGraph
    ) -> bool:
        """恢复到指定恢复点"""
        return self.backup_manager.restore_backup(recovery_point_id, kg)
    
    def create_disaster_recovery_plan(self) -> Dict[str, Any]:
        """创建灾难恢复计划文档"""
        backups = self.backup_manager.list_backups()
        
        plan = {
            "created_at": get_timestamp(),
            "backup_count": len(backups),
            "latest_backup": backups[0].backup_id if backups else None,
            "recovery_points": self.recovery_points,
            "steps": [
                "1. Stop current agent instance",
                "2. Identify latest valid backup",
                "3. Restore backup to knowledge_graph.json",
                "4. Restart agent",
                "5. Verify data integrity",
                "6. Resume normal operation"
            ],
            "estimated_recovery_time": "5-10 minutes",
            "potential_data_loss": "Last backup interval (typically 1 hour)"
        }
        
        return plan
    
    def test_recovery(self, kg: KnowledgeGraph) -> bool:
        """测试恢复流程"""
        try:
            logger.info("Starting disaster recovery test...")
            
            # 创建测试数据
            test_node = "disaster_recovery_test"
            kg.add_node(test_node, {"test": "disaster recovery"})
            
            # 创建恢复点
            if not self.create_recovery_point(kg, "Test recovery"):
                logger.error("Failed to create test recovery point")
                return False
            
            # 删除测试数据
            kg.remove_node(test_node)
            kg.force_save()
            
            # 恢复
            recovery_points = self.list_recovery_points()
            if not recovery_points:
                logger.error("No recovery points found")
                return False
            
            latest_point = recovery_points[0]["recovery_point_id"]
            success = self.restore_to_point(latest_point, kg)
            
            # 验证
            if success and test_node in kg.nodes:
                logger.info("Disaster recovery test successful")
                return True
            else:
                logger.error("Disaster recovery test failed")
                return False
                
        except Exception as e:
            logger.error(f"Disaster recovery test failed: {e}")
            return False

# ========================================
# 综合可靠性管理器
# ========================================

class ReliabilityManager:
    """综合可靠性管理器"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        
        # 初始化所有管理器
        self.backup_manager = BackupManager()
        self.storage = MultiFileStorage()
        self.health_checker = EnhancedHealthChecker(kg)
        self.shutdown_manager = GracefulShutdownManager(kg)
        self.resource_monitor = ResourceMonitor()
        
        # 实例和故障转移
        instance_id = f"agent_{os.uname().nodename}_{os.getpid()}"
        self.instance_manager = InstanceManager(instance_id)
        self.instance_manager.register_instance()
        
        self.failover_manager = FailoverManager(self.instance_manager)
        self.disaster_recovery = DisasterRecoveryManager(self.backup_manager)
        
        # 数据完整性
        self.integrity_checker = DataIntegrityChecker(kg)
    
    def perform_maintenance(self) -> Dict[str, Any]:
        """
        执行维护任务
        """
        results = {
            "timestamp": get_timestamp(),
            "actions": []
        }
        
        # 1. 检查完整性
        integrity = self.integrity_checker.check_integrity()
        results["actions"].append({
            "action": "integrity_check",
            "issues": integrity.get("stats", {}).get("issues_count", 0),
            "warnings": integrity.get("stats", {}).get("warnings_count", 0)
        })
        
        # 2. 自动修复
        repairs = self.integrity_checker.auto_repair()
        if repairs > 0:
            results["actions"].append({
                "action": "auto_repair",
                "repairs": repairs
            })
        
        # 3. 健康检查
        health = self.health_checker.perform_health_check()
        results["actions"].append({
            "action": "health_check",
            "status": health.status,
            "score": health.score
        })
        
        # 4. 自动备份
        backup = self.backup_manager.create_backup(self.kg)
        if backup:
            results["actions"].append({
                "action": "backup",
                "backup_id": backup.backup_id
            })
        
        # 5. 心跳
        heartbeat = self.instance_manager.heartbeat()
        results["actions"].append(heartbeat)
        
        # 6. 检查故障转移
        if self.failover_manager.check_failover_needed():
            self.failover_manager.perform_failover()
            results["actions"].append({
                "action": "failover_performed"
            })
        
        logger.info(f"Maintenance completed: {len(results['actions'])} actions performed")
        return results
    
    def get_full_report(self) -> Dict[str, Any]:
        """获取完整可靠性报告"""
        return {
            "health": asdict(self.health_checker.perform_health_check()),
            "backups": [asdict(b) for b in self.backup_manager.list_backups()[:5]],
            "integrity": self.integrity_checker.check_integrity(),
            "resources": self.resource_monitor.check_resources(),
            "failover_stats": self.failover_manager.get_failover_stats(),
            "recovery_plan": self.disaster_recovery.create_disaster_recovery_plan()
        }
