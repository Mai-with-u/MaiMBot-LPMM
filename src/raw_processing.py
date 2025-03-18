import json
import os

from config import global_config
from utils import get_md5


def load_raw_data(logger) -> dict:
    """加载import.json文件"""
    # 读取import.json文件
    logger.info("正在读取import.json文件")
    if os.path.exists(global_config.import_file) is True:
        with open(global_config.import_file, "r", encoding="utf-8") as f:
            import_json = json.loads(f.read())
    else:
        import_json = None
    # import_json内容示例：
    # import_json = [
    #       "The capital of China is Beijing. The capital of France is Paris.",
    # ]
    if import_json is None:
        logger.error("import.json文件为空/不存在/格式错误")
        return
    else:
        logger.info("import.json文件读取成功")
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
