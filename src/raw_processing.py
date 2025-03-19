import json
import os

from .config import global_config
from .utils import get_md5
from global_logger import logger


def load_raw_data() -> dict:
    """加载import.json文件"""
    # 读取import.json文件
    logger.info("正在读取import.json文件")
    if os.path.exists(global_config["persistence"]["raw_data_path"]) is True:
        with open(
            global_config["persistence"]["raw_data_path"], "r", encoding="utf-8"
        ) as f:
            import_json = json.loads(f.read())
    else:
        import_json = None
    # import_json内容示例：
    # import_json = [
    #       "The capital of China is Beijing. The capital of France is Paris.",
    # ]
    if import_json is None:
        logger.error("原始数据文件为空/不存在/格式错误")
        return
    else:
        logger.info("原始数据文件读取成功")
        raw_data = {}
        md5_set = set()
        for item in import_json:
            hash = get_md5(item)
            if hash in md5_set:
                logger.warning("重复数据：{}".format(item))
                continue
            md5_set.add(hash)
            raw_data[hash] = item
        logger.info("共读取到{}条数据".format(len(raw_data)))

    return raw_data, md5_set
