import json
import os
import time

import tqdm

from .llm_client import LLMClient
from . import prompt_template
from .config import global_config
from global_logger import logger


def _entity_extract(llm_client: LLMClient, paragraph: str):
    """对段落进行实体提取，返回提取出的实体列表（JSON格式）"""
    entity_extract_context = prompt_template.build_entity_extract_context(paragraph)
    request_result = llm_client.send_chat_request(
        global_config["entity_extract"]["llm"]["model"], entity_extract_context
    )

    # 截取</think>标签后的内容
    if "</think>" in request_result:
        request_result = request_result.split("</think>")[1]

    # 去除‘{’前的内容（结果中可能有多个‘{’）
    if "{" in request_result:
        request_result = request_result[request_result.index("{") :]

    # 去除最后一个‘}’后的内容（结果中可能有多个‘}’）
    if "}" in request_result:
        request_result = request_result[: request_result.rindex("}") + 1]

    entity_extract_result = json.loads(request_result)
    return entity_extract_result


def process_entity_extract(llm_client: LLMClient, raw_data: dict, md5_set: set):
    """处理实体提取任务"""
    # 读取entity_output.json文件
    logger.info("正在读取Entity文件")
    entity_file = global_config["persistence"]["entity_data_path"]
    entity_json = None
    if os.path.exists(entity_file) is True:
        with open(entity_file, "r", encoding="utf-8") as f:
            try:
                entity_json = json.loads(f.read())
            except json.JSONDecodeError:
                entity_json = None
    # entity_json内容示例：
    # entity_json = {
    #     "0": ["China", "Beijing", "France", "Paris"],
    # }

    if entity_json is None:
        logger.warning("Entity文件为空/不存在/格式错误")
        logger.info("开始执行实体提取任务")
        # 执行实体提取任务
        skip_ids = []  # 存储跳过的id
        entity_json = {}  # 存储实体提取的结果
        for item in tqdm.tqdm(
            raw_data, total=len(raw_data), desc="实体提取任务进度:", leave=False
        ):
            try_count = 0
            while try_count < 3:
                try:
                    extracted_entity_json = _entity_extract(llm_client, raw_data[item])
                    entity_json[item] = extracted_entity_json["named_entities"]
                    break
                except Exception as e:
                    logger.error("实体提取任务失败，原因：{}".format(e))
                    logger.warning("于5s后重试实体提取请求...")
                    try_count += 1
                    time.sleep(5)
            if try_count == 3:
                logger.error("实体提取任务失败，已重试3次，跳过此条数据")
                skip_ids.append(item)
                continue
        # 将实体提取的结果写回entity_output.json文件
        with open(entity_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(entity_json, ensure_ascii=False))
        logger.info("实体提取任务完成.")
        if len(skip_ids) > 0:
            logger.warning("以下id的数据未能提取实体，已跳过：{}".format(skip_ids))
    else:
        logger.info("Entity文件读取成功")
        # 检查是否有未提取的实体
        update_flag = False
        skip_ids = []  # 存储跳过的id
        for item in tqdm.tqdm(
            md5_set, total=len(md5_set), desc="实体提取检查进度:", leave=False
        ):
            if item not in entity_json:
                update_flag = True
                logger.info("发现未提取的文段，重新执行实体提取任务")
                try_count = 0
                while try_count < 3:
                    try:
                        extracted_entity_json = _entity_extract(
                            llm_client, raw_data[item]
                        )
                        entity_json[item] = extracted_entity_json["named_entities"]
                        break
                    except Exception as e:
                        logger.error("实体提取任务失败，原因：{}".format(e))
                        logger.warning("于5s后重试实体提取请求...")
                        try_count += 1
                        time.sleep(5)
                if try_count == 3:
                    logger.error("实体提取任务失败，已重试3次，跳过此条数据")
                    skip_ids.append(item)
                    continue

        if update_flag:
            # 将实体提取的结果写回entity_output.json文件
            with open(entity_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(entity_json, ensure_ascii=False))

        logger.info("实体提取任务完成.")
        if len(skip_ids) > 0:
            logger.warning("以下id的数据未能提取实体，已跳过：{}".format(skip_ids))

    return entity_json
