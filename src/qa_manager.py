import time

from global_logger import logger
from src import prompt_template
from src.embedding_store import EmbeddingManager
from src.llm_client import LLMClient
from src.rag_processing import KGManager
from src.config import global_config


class QAManager:
    def __init__(
        self,
        embed_manager: EmbeddingManager,
        kg_manager: KGManager,
        llm_client_embedding: LLMClient,
        llm_client_filter: LLMClient,
        llm_client_qa: LLMClient,
    ):
        self.embed_manager = embed_manager
        self.kg_manager = kg_manager
        self.llm_client_list = {
            "embedding": llm_client_embedding,
            "filter": llm_client_filter,
            "qa": llm_client_qa,
        }

    def process_query(self, question: str) -> str:
        """处理查询"""
        start_time = time.time()  # 计时：总用时计算
        part_start_time = start_time  # 计时：部分用时计算

        # 生成问题的Embedding
        question_embedding = self.llm_client_list["embedding"].send_embedding_request(
            global_config["embedding"]["model"], question
        )
        logger.info(f"Embedding用时：{time.time() - part_start_time:.2f}s")
        part_start_time = time.time()

        # 根据问题Embedding查询Relation Embedding
        relation_search_res = self.embed_manager.relation_embedding_store.search_top_k(
            question_embedding,
            global_config["qa"]["params"]["relation_search_top_k"],
        )
        # 过滤阈值
        # 考虑动态阈值：当存在显著数值差异的结果时，保留显著结果；否则，保留所有结果
        relation_search_res = [
            (
                tuple(
                    self.embed_manager.relation_embedding_store.store[res[0]]
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

        paragraph_search_res = (
            self.embed_manager.paragraphs_embedding_store.search_top_k(
                question_embedding,
                global_config["qa"]["params"]["paragraph_search_top_k"],
            )
        )
        logger.info(f"文段检索用时：{time.time() - part_start_time:.2f}s")
        part_start_time = time.time()

        if len(relation_search_res) != 0:
            logger.info("找到相关关系，将使用RAG进行检索")
            # 使用KG检索
            result = self.kg_manager.kg_search(
                relation_search_res, paragraph_search_res
            )
            idx_with_score = [(item[0], item[2]) for item in result]
            result = [(item[1], item[2]) for item in result]
            logger.info(f"RAG检索用时：{time.time() - part_start_time:.2f}s")
            part_start_time = time.time()
        else:
            logger.info("未找到相关关系，将使用文段检索结果")
            result = paragraph_search_res
        result = result[: global_config["qa"]["params"]["res_top_k"]]

        for res in result:
            raw_paragraph = self.embed_manager.paragraphs_embedding_store.store[
                res[0]
            ].str
            print(f"找到相关文段，相关系数：{res[1]:.8f}\n{raw_paragraph}\n\n")

        knowledge = [
            (
                self.embed_manager.paragraphs_embedding_store.store[res[0]].str,
                res[1],
            )
            for res in result
        ]
        # 将检索结果和问题发送给LLM，获取答案
        # 构造上下文
        context = prompt_template.build_qa_context(question, knowledge)
        reasoning, content = self.llm_client_list["qa"].send_chat_request(
            global_config["qa"]["llm"]["model"], context
        )
        if reasoning is None:
            print(f"回答：{content}\n")
        else:
            print(f"思考：{reasoning}\n回答：{content}\n")

        logger.info(f"总用时：{time.time() - start_time:.2f}s")
