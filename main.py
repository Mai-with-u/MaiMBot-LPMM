import sys
from typing import Dict, List

from src.config import PG_NAMESPACE, global_config
from src.embedding_store import EmbeddingManager
from src.llm_client import LLMClient
from src.open_ie import get_openie_obj
from src.rag_processing import RAGManager
from global_logger import logger
from src.utils import get_md5


def hash_deduplicate_and_reindex(
    raw_paragraphs: Dict[str, str],
    triple_list_data: Dict[str, List[List[str]]],
    stored_pg_hashes: set,
    stored_paragraph_hashes: set,
):
    """Hash去重与重索引"""
    # 保存去重后的段落
    new_raw_paragraphs = dict()
    # 保存新的三元组
    new_triple_list_data = dict()

    for _, (raw_paragraph, triple_list) in enumerate(
        zip(raw_paragraphs.values(), triple_list_data.values())
    ):
        # 段落hash
        paragraph_hash = get_md5(raw_paragraph)
        if ((PG_NAMESPACE + "-" + paragraph_hash) in stored_pg_hashes) and (
            paragraph_hash in stored_paragraph_hashes
        ):
            continue
        new_raw_paragraphs[paragraph_hash] = raw_paragraph
        new_triple_list_data[paragraph_hash] = triple_list

    return new_raw_paragraphs, new_triple_list_data


def main():
    logger.info("----启动Mai-HippoRAG2 Demo----\n")

    logger.info("创建LLM客户端")
    llm_client_list = dict()

    for key in global_config["llm_providers"]:
        llm_client_list[key] = LLMClient(
            global_config["llm_providers"][key]["base_url"],
            global_config["llm_providers"][key]["api_key"],
        )

    # 获取OpenIE对象
    openie_obj = get_openie_obj(llm_client_list)

    # 重组织openie结果
    # 索引的段落原文
    raw_paragraphs = openie_obj.extract_raw_paragraph_dict()
    # 索引的实体列表
    entity_list_data = openie_obj.extract_entity_dict()
    # 索引的三元组列表
    triple_list_data = openie_obj.extract_triple_dict()

    # 检查数据是否有异常
    assert (
        len(openie_obj.docs) > 0
        and len(openie_obj.docs) == len(entity_list_data)
        and len(openie_obj.docs) == len(triple_list_data)
    ), "数据异常"

    del entity_list_data, openie_obj

    embed_manager = embed_manager = EmbeddingManager(
        llm_client_list[global_config["embedding"]["provider"]]
    )
    logger.info("正在从文件加载Embedding库")
    try:
        embed_manager.load_from_file()
    except Exception as e:
        logger.error("从文件加载Embedding库时发生错误：{}".format(e))
    logger.info("Embedding库加载完成")

    rag_manager = RAGManager()
    logger.info("正在从文件加载RAG")
    try:
        rag_manager.load_from_file()
    except Exception as e:
        logger.error("从文件加载RAG时发生错误：{}".format(e))
    logger.info("RAG加载完成")

    # 将索引换为对应段落的hash值
    logger.info("正在进行段落去重与重索引")
    raw_paragraphs, triple_list_data = hash_deduplicate_and_reindex(
        raw_paragraphs,
        triple_list_data,
        embed_manager.stored_pg_hashes,
        rag_manager.stored_paragraph_hashes,
    )

    if len(raw_paragraphs) != 0:
        # 获取嵌入并保存
        logger.info(f"段落去重完成，剩余待处理的段落数量：{len(raw_paragraphs)}")
        logger.info("开始Embedding")
        embed_manager.store_pg_into_embedding(raw_paragraphs)
        embed_manager.store_ent_into_embedding(triple_list_data)
        embed_manager.store_rel_into_embedding(triple_list_data)
        embed_manager.save_to_file()
        logger.info("Embedding完成")
        # 构建新段落的RAG
        logger.info("开始构建RAG")
        rag_manager.build_rag(triple_list_data)
        rag_manager.save_to_file()
        logger.info("RAG构建完成")
        # 进行同义词连接
        logger.info("开始同义词连接")
        rag_manager.synonym_connect()
        rag_manager.save_to_file()
        logger.info("同义词连接完成")
    else:
        logger.info("无新段落需要处理")

    return

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
