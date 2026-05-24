#!/usr/bin/env python3
"""
快速演示 - 运行一小会儿然后展示知识图谱
"""
import time
import threading
import sys

from eternal_agent.agent import EternalSelfAgent
from eternal_agent.task_queue import GLOBAL_TASK_QUEUE
from eternal_agent.utils import logger


# 运行时间（秒）
RUN_DURATION = 5


def stop_agent(agent):
    """在指定时间后停止agent"""
    time.sleep(RUN_DURATION)
    agent.system_alive = False
    logger.info("Demo duration reached. Stopping agent...")


def main():
    logger.info("=" * 50)
    logger.info("永动知识图谱Agent 快速演示")
    logger.info(f"将运行 {RUN_DURATION} 秒...")
    logger.info("=" * 50)
    
    # 初始化
    agent = EternalSelfAgent()
    
    # 注入初始任务
    initial_task = "系统初始认知迭代"
    GLOBAL_TASK_QUEUE.add(initial_task)
    logger.info(f"添加初始任务: {initial_task}")
    
    # 在后台线程停止agent
    stop_thread = threading.Thread(target=stop_agent, args=(agent,))
    stop_thread.daemon = True
    stop_thread.start()
    
    # 运行
    try:
        agent.eternal_loop()
    except SystemExit:
        pass
    
    # 展示结果
    logger.info("\n" + "=" * 50)
    logger.info("演示结束！知识图谱统计:")
    stats = agent.knowledge_graph.get_stats()
    logger.info(f"  - 节点数: {stats['nodes_count']}")
    logger.info(f"  - 边数: {stats['edges_count']}")
    logger.info(f"  - 运行步数: {agent.run_counter}")
    logger.info("=" * 50)
    
    logger.info("\n知识图谱内容:")
    for node_name in agent.knowledge_graph.nodes:
        logger.info(f"  节点: {node_name}")
    for edge in agent.knowledge_graph.edges:
        logger.info(f"  边: {edge.source} -> {edge.target} ({edge.relation_name}, w={edge.weight})")


if __name__ == "__main__":
    main()
