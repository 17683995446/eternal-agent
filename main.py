#!/usr/bin/env python3
"""
阶段5：项目入口框架
阶段64：系统唯一启动入口
"""
import signal
import sys

from eternal_agent.agent import EternalSelfAgent
from eternal_agent.task_queue import GLOBAL_TASK_QUEUE
from eternal_agent.utils import logger


def signal_handler(sig, frame):
    """处理优雅关闭"""
    logger.info("Received shutdown signal. Preparing to stop...")
    sys.exit(0)


def main_entry():
    """
    系统唯一启动入口
    """
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 50)
    logger.info("基于第一性原理 · 轻量化永动知识图谱Agent")
    logger.info("=" * 50)
    
    # 初始化智能体
    agent = EternalSelfAgent()
    
    # 注入初始根认知任务，启动自驱闭环原点
    initial_task = "系统初始认知迭代"
    GLOBAL_TASK_QUEUE.add(initial_task)
    logger.info(f"Added initial task: {initial_task}")
    
    # 启动永久循环
    try:
        agent.eternal_loop()
    except KeyboardInterrupt:
        logger.info("System stopped by user.")
    except Exception as e:
        logger.error(f"System stopped with error: {e}")
        raise


if __name__ == "__main__":
    main_entry()
