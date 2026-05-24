"""
阶段3：基础文件操作工具
"""
import json
import time
import logging
from typing import Any, Dict, List, Optional

# 基础日志功能
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EternalAgent")


def save_json(data: Any, file_path: str) -> None:
    """保存数据到JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        raise


def load_json(file_path: str) -> Optional[Any]:
    """从JSON文件加载数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        raise


def get_timestamp() -> float:
    """获取当前时间戳"""
    return time.time()


def format_timestamp(timestamp: float) -> str:
    """格式化时间戳"""
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
