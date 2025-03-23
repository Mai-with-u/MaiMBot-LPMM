import sys
import time
from typing import Dict, List
import igraph as ig

from src import prompt_template
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
    logger.info("----启动Mai-LPMM Demo----\n")

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
        embed_manager.store_new_data_set(raw_paragraphs, triple_list_data)
        embed_manager.save_to_file()
        logger.info("Embedding完成")
        # Embedding-Faiss重索引
        logger.info("正在重新构建Embedding向量索引")
        embed_manager.rebuild_faiss_index()
        logger.info("向量索引构建完成")
        # 构建新段落的RAG
        logger.info("开始构建RAG")
        rag_manager.build_rag(triple_list_data, embed_manager)
        rag_manager.save_to_file()
        logger.info("RAG构建完成")
    else:
        logger.info("无新段落需要处理")

    # 将RAG图输出到svg文件
    ig.plot(rag_manager.graph, bbox=(0, 0, 1920, 1080)).save("RAG.png")

    logger.info("------------开始QA------------")
    while True:
        print("请在此处输入问题，输入exit退出：", end="")
        sys.stdout.flush()
        question = input().strip()
        if question == "exit":
            break
        if question == "":
            continue

        start_time = time.time()  # 计时：总用时计算
        part_start_time = start_time  # 计时：部分用时计算

        # 生成问题的Embedding
        question_embedding = llm_client_list[
            global_config["embedding"]["provider"]
        ].send_embedding_request(global_config["embedding"]["model"], question)

        logger.info(f"Embedding用时：{time.time() - part_start_time:.2f}s")
        part_start_time = time.time()

        # 根据问题Embedding查询Relation Embedding
        relation_search_res = embed_manager.relation_embedding_store.search_top_k(
            question_embedding, global_config["qa"]["params"]["relation_search_top_k"]
        )
        # 过滤阈值
        # 考虑动态阈值：当存在显著数值差异的结果时，保留显著结果；否则，保留所有结果
        relation_search_res = [
            (
                tuple(
                    embed_manager.relation_embedding_store.store[res[0]]
                    .str[1:-1]
                    .split(", ")
                ),
                res[1],
            )
            for res in relation_search_res
            if res[1] >= global_config["qa"]["params"]["relation_threshold"]
        ]

        logger.info(f"关系检索用时：{time.time() - part_start_time:.2f}s")
        part_start_time = time.time()

        for res in relation_search_res:
            print(f"找到相关关系，相似度：{(res[1] * 100):.2f}%  -  {res[0]}")

        # TODO: 使用LLM过滤三元组结果
        # logger.info(f"LLM过滤三元组用时：{time.time() - part_start_time:.2f}s")
        # part_start_time = time.time()

        paragraph_search_res = embed_manager.paragraphs_embedding_store.search_top_k(
            question_embedding, global_config["qa"]["params"]["paragraph_search_top_k"]
        )

        logger.info(f"文段检索用时：{time.time() - part_start_time:.2f}s")
        part_start_time = time.time()

        if len(relation_search_res) != 0:
            logger.info("找到相关关系，将使用RAG进行检索")
            # 使用RAG检索
            result = rag_manager.rag_search_and_pr(
                relation_search_res, paragraph_search_res
            )
            logger.info(f"RAG检索用时：{time.time() - part_start_time:.2f}s")
            part_start_time = time.time()
        else:
            logger.info("未找到相关关系，将使用文段检索结果")
            result = paragraph_search_res

        result = result[: global_config["qa"]["params"]["res_top_k"]]

        for res in result:
            raw_paragraph = embed_manager.paragraphs_embedding_store.store[res[0]].str
            print(f"找到相关文段，相关系数：{res[1]:.8f}\n{raw_paragraph}\n\n")

        knowledge = [
            (embed_manager.paragraphs_embedding_store.store[res[0]].str, res[1])
            for res in result
        ]

        # 将检索结果和问题发送给LLM，获取答案

        # 构造上下文

        context = prompt_template.build_qa_context(question, knowledge)
        ret = llm_client_list[global_config["qa"]["llm"]["provider"]].send_chat_request(
            global_config["qa"]["llm"]["model"], context
        )

        # 去掉头部的 <think> 标签
        ret = ret.split("<think>")[-1]
        ret = ret.split("</think>")
        print(f"思考：{ret[0]}\n回答：{ret[1]}\n")

        logger.info(f"总用时：{time.time() - start_time:.2f}s")

    logger.info("----结束Mai-LPMM Demo----")


if __name__ == "__main__":
    main()
