import logging
import json
import os
import sys

from .src.config import global_config
from .src.llm_client import LLMClient
from .src.entity_processing import process_entity_extract
from .src.open_ie import OpenIE
from .src.raw_processing import load_raw_data
from .src.rdf_processing import process_rdf_extract
from .src.rag_processing import RAG

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("----启动Mai-HippoRAG2 Demo----\n")

    logger.info("创建LLM客户端")
    llm_client = LLMClient(
        global_config.llm_base_url, global_config.entity_extract_llm_key
    )

    # 检查OpenIE文件是否存在
    openie_obj = None
    if os.path.exists(global_config.openie_file):
        try:
            with open(global_config.openie_file, "r", encoding="utf-8") as f:
                openie_obj = json.loads(f.read())
            openie_obj = OpenIE.from_dict(openie_obj)
        except Exception as e:
            logger.error("OpenIE文件存在错误：{}".format(e))
            openie_obj = None

    if openie_obj is not None:
        logger.info("OpenIE文件已存在，跳过实体提取、RDF构建、RAG构建任务")
    else:
        logger.info(
            "OpenIE文件为空/不存在/格式错误，开始执行实体提取、RDF构建、RAG构建任务"
        )

        # 加载import.json文件
        raw_data, md5_set = load_raw_data(logger)

        # 加载实体提取结果
        entities_json = process_entity_extract(logger, llm_client, raw_data, md5_set)

        # 加载RDF结果
        rdf_json = process_rdf_extract(
            logger, llm_client, raw_data, md5_set, entities_json
        )

        # 转换并保存为OpenIE样式
        logger.info("正在将数据保存为OpenIE格式")
        openie_docs = []
        for item in raw_data:
            if item in entities_json and item in rdf_json:
                openie_docs.append(
                    {
                        "idx": item,
                        "passage": raw_data[item],
                        "extracted_entities": entities_json[item],
                        "extracted_triples": rdf_json[item],
                    }
                )
        openie_obj = OpenIE.from_all_docs(openie_docs)
        openie_obj.save_data_as_openie_format()
        logger.info("OpenIE文件保存成功")

    # 构建RAG
    rag = RAG.build_rag(logger, llm_client, openie_obj)

    if global_config.qa:
        logger.info("开始QA:")
        print("请在此处输入问题，输入exit退出：", end="")
        sys.stdout.flush()
        while True:
            question = input()
            if question == "exit":
                break
            # 检索知识库
            # 生成回答
            # context = prompt_template.build_qa_context(question, rag.get_knowledge(question))
            # response = llm_client.send_chat_request()
            # answer = response.choices[0].message.content
            # print("回答：", answer)
            print("请继续输入问题，输入exit退出：", end="")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
