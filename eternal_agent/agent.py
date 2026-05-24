"""
阶段21-40 + 阶段42-50：内核层 - 永续自治智能体主体
+ 完整测试、性能优化、配置管理、监控指标、可视化
"""
import time
from typing import Optional
import traceback
import sys

from .constants import LOOP_DELAY, EVOLVE_STEP, DEFAULT_EDGE_WEIGHT
from .knowledge_graph import KnowledgeGraph
from .task_queue import GLOBAL_TASK_QUEUE
from .utils import logger
from .config import global_config
from .metrics import global_metrics


class EternalSelfAgent:
    """
    核心类：永续自治智能体
    实现三大公理：存续、记忆、自驱
    """

    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.run_counter = 0
        self.system_alive = True
        self._loop_delay = global_config.get("loop_delay", LOOP_DELAY)
        self._evolve_step = global_config.get("evolve_step", EVOLVE_STEP)

    def health_check(self) -> None:
        """
        阶段22：存续公理 - 周期自检 + 周期性触发知识进化
        """
        self.run_counter += 1
        
        # 每固定步数自动精简知识、迭代认知
        if self.run_counter % self._evolve_step == 0:
            logger.info(f"Evolution trigger at step {self.run_counter}")
            self.knowledge_graph.trim_invalid_knowledge()
            
            # 阶段47：控制台可视化 - 打印统计
            self._print_status()

    def _print_status(self) -> None:
        """阶段47：控制台可视化 - 打印当前状态"""
        kg_stats = self.knowledge_graph.get_stats()
        full_stats = global_metrics.get_stats(kg_stats)
        
        status_line = (
            f"[Step {self.run_counter}] "
            f"Nodes: {full_stats['nodes_count']}, "
            f"Edges: {full_stats['edges_count']}, "
            f"Tasks: {full_stats['total_tasks_executed']}, "
            f"Uptime: {full_stats['uptime_seconds']}s"
        )
        logger.info(status_line)

    def self_repair(self) -> None:
        """
        阶段23：存续公理 - 故障自愈、异常隔离
        """
        global_metrics.update_exception_count()
        logger.warning("Performing self-repair...")
        time.sleep(0.5)  # 短时休眠
        # 重置运行状态
        # 这里可以添加更多的恢复逻辑

    def get_current_task(self) -> Optional[str]:
        """
        阶段24：获取当前待执行任务
        """
        if not GLOBAL_TASK_QUEUE.is_empty():
            return GLOBAL_TASK_QUEUE.pop()
        return None

    def idle_self_evolve(self) -> None:
        """
        阶段25：自驱公理 - 空闲时自动复盘、梳理知识
        """
        # 系统静默休眠，维持循环不退出
        time.sleep(self._loop_delay * 2)

    def execute_task(self, task: str) -> None:
        """
        阶段33-36：核心闭环 - 任务执行 -> 沉淀知识 -> 生成新任务
        """
        global_metrics.update_task_count()
        logger.info(f"Executing task: {task}")
        
        # 1. 调取历史知识辅助当前决策
        derive_tasks = self.knowledge_graph.derive_new_tasks(task)
        if derive_tasks:
            logger.debug(f"Derived {len(derive_tasks)} tasks from knowledge")
        
        # 2. 本次任务行为沉淀为新知识
        self.knowledge_graph.add_node(task)
        next_iter_task = f"系统迭代任务_{self.run_counter}"
        self.knowledge_graph.add_edge(
            source=task,
            target=next_iter_task,
            relation_name="自主衍生"
        )
        
        # 3. 知识驱动自驱：新生任务入队，维持永动闭环
        GLOBAL_TASK_QUEUE.add(next_iter_task)
        added = GLOBAL_TASK_QUEUE.batch_add(derive_tasks)
        if added > 0:
            logger.debug(f"Added {added} derived tasks to queue")

    def eternal_loop(self) -> None:
        """
        阶段26：终极永动循环（系统心脏，永不退出）
        """
        logger.info("Starting eternal loop...")
        logger.info(f"Config: {global_config.get_all()}")
        
        while self.system_alive:
            try:
                self.health_check()
                task = self.get_current_task()
                
                if task is None:
                    # 无任务 -> 空闲进化模式
                    self.idle_self_evolve()
                    continue
                
                # 有任务 -> 执行并产生新知识、新任务
                self.execute_task(task)
                time.sleep(self._loop_delay)
                
            # 阶段27：全局异常捕获 - 任何错误不击穿系统
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.shutdown()
                break
            except Exception as e:
                logger.error(f"Exception in loop: {e}")
                logger.debug(traceback.format_exc())
                self.self_repair()

    def shutdown(self) -> None:
        """优雅关闭 - 保存最终状态"""
        logger.info("Shutting down...")
        self.knowledge_graph.force_save()
        self._print_status()
        logger.info("Goodbye!")
        self.system_alive = False
