"""
阶段2：核心常量定义（公理固化）
"""

# 存续公理：主循环节拍，控CPU、防卡死、稳态运行
LOOP_DELAY = 0.3

# 自驱公理：固定迭代步数，周期性触发知识进化
EVOLVE_STEP = 50

# 记忆公理：唯一持久化文件入口
KG_SAVE_PATH = "knowledge_graph.json"

# 资源守恒公理：限制任务池上限，杜绝无限膨胀
TASK_QUEUE_MAX = 200

# 知识权重阈值
MIN_WEIGHT_FOR_DERIVE = 0.2
MIN_WEIGHT_FOR_KEEP = 0.1

# 默认边权重默认值
DEFAULT_EDGE_WEIGHT = 0.8
