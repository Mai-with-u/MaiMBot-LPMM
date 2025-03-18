import json
import os
import time

from llm_client import LLMClient
import prompt_template
from config import global_config


def rdf_triple_extract(llm_client: LLMClient, paragraph: str, entities: list):
    """对段落进行实体提取，返回提取出的实体列表（JSON格式）"""
    entity_extract_context = prompt_template.build_rdf_triple_extract_context(
        paragraph, entities=json.dumps(entities, ensure_ascii=False)
    )
    request_result = llm_client.send_chat_request(
        global_config.entity_extract_llm_type, entity_extract_context
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


def process_rdf_extract(
    logger,
    llm_client: LLMClient,
    raw_data: dict,
    md5_set: set,
    entities_json: dict,
):
    # 该任务需要读取RDF的结果，所以需要读取rdf_output.json文件
    logger.info("正在读取rdf_output.json文件")
    rdf_file = global_config.rdf_file
    rdf_json = None
    if os.path.exists(rdf_file) is True:
        with open(rdf_file, "r", encoding="utf-8") as f:
            try:
                rdf_json = json.loads(f.read())
            except json.JSONDecodeError:
                rdf_json = None
    # entity_json内容示例：
    # entity_json = {
    #     "0": ["China", "Beijing", "France", "Paris"],
    # }

    if (rdf_json is None) or (len(rdf_json) == 0):
        logger.error("rdf_output.csv文件为空/不存在/格式错误")
        # 构建RDF
        logger.info("开始执行RDF构建任务")
        skip_ids = []
        rdf_json = {}
        for item in raw_data:
            try_count = 0
            while try_count < 3:
                try:
                    extracted_rdf = rdf_triple_extract(
                        global_config,
                        llm_client,
                        raw_data[item],
                        entities_json[item],
                    )
                    print(extracted_rdf)
                    rdf_json[item] = extracted_rdf["triples"]
                    break
                except Exception as e:
                    logger.error("RDF构建任务失败，原因：{}".format(e))
                    logger.warning("于5s后重试RDF构建请求...")
                    try_count += 1
                    time.sleep(5)
            if try_count == 3:
                logger.error("RDF构建任务失败，已重试3次，跳过此条数据")
                skip_ids.append(item)
                continue
        # 将RDF写回rdf_output.csv文件
        with open(rdf_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(rdf_json, ensure_ascii=False))

        logger.info("RDF构建任务完成.")
        if len(skip_ids) > 0:
            logger.warning("以下id的数据未能提取RDF，已跳过：{}".format(skip_ids))
    else:
        logger.info("rdf_output.csv文件读取成功")
        # 检查是否有未提取的RDF
        update_flag = False
        skip_ids = []  # 存储跳过的id
        for item in md5_set:
            if item not in rdf_json:
                update_flag = True
                logger.info("发现未提取的文段，重新执行RDF提取任务")
                try_count = 0
                while try_count < 3:
                    try:
                        extracted_rdf = rdf_triple_extract(
                            global_config,
                            llm_client,
                            raw_data[item],
                            entities_json[item],
                        )
                        print(extracted_rdf)
                        rdf_json[item] = extracted_rdf["triples"]
                        break
                    except Exception as e:
                        logger.error("RDF构建任务失败，原因：{}".format(e))
                        logger.warning("于5s后重试RDF构建请求...")
                        try_count += 1
                        time.sleep(5)
                if try_count == 3:
                    logger.error("RDF构建任务失败，已重试3次，跳过此条数据")
                    skip_ids.append(item)
                    continue

        if update_flag:
            # 将实体提取的结果写回entity_output.json文件
            with open(rdf_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(rdf_json, ensure_ascii=False))

        logger.info("RDF构建任务完成.")
        if len(skip_ids) > 0:
            logger.warning("以下id的数据未能提取RDF，已跳过：{}".format(skip_ids))

    return rdf_json
