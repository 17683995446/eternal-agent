"""
阶段4：任务队列基础实现
"""
from typing import List, Optional
from .constants import TASK_QUEUE_MAX


class BoundedTaskQueue:
    """有限长度任务队列 - 资源守恒公理"""

    def __init__(self, max_size: int = TASK_QUEUE_MAX):
        self.max_size = max_size
        self._queue: List[str] = []

    def add(self, task: str) -> bool:
        """添加任务到队列，返回是否成功"""
        if len(self._queue) >= self.max_size:
            return False
        self._queue.append(task)
        return True

    def batch_add(self, tasks: List[str]) -> int:
        """批量添加任务，返回实际添加数量"""
        added = 0
        for task in tasks:
            if self.add(task):
                added += 1
            else:
                break
        return added

    def pop(self) -> Optional[str]:
        """从队首弹出任务"""
        if not self._queue:
            return None
        return self._queue.pop(0)

    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return len(self._queue) == 0

    def size(self) -> int:
        """获取队列长度"""
        return len(self._queue)

    def clear(self) -> None:
        """清空队列"""
        self._queue.clear()

    def get_all(self) -> List[str]:
        """获取所有任务（用于调试）"""
        return list(self._queue)


# 全局任务队列：系统唯一驱动源
GLOBAL_TASK_QUEUE = BoundedTaskQueue()
