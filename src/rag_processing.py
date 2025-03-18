from typing import Dict, List
from llm_client import LLMClient
from open_ie import OpenIE
from src.embedding_store import EmbeddingStore
from config import global_config

from main import logger

PG_NAMESPACE = "paragraph"
ENT_NAMESPACE = "entity"
REL_NAMESPACE = "relation"


class RAG:
    def __init__(self, llm_client: LLMClient):
        self.paragraphs_embedding_store = EmbeddingStore(llm_client, PG_NAMESPACE)
        self.entities_embedding_store = EmbeddingStore(llm_client, ENT_NAMESPACE)
        self.relation_embedding_store = EmbeddingStore(llm_client, REL_NAMESPACE)

        # 存储段落的hash值，用于去重
        self.stored_paragraph_hashes = set()

        # 实体之间的联系
        self.node_to_node = dict()
        # 实体出现次数统计，用于计算权重
        self.ent_appear_cnt = dict()

    def load_from_file(self):
        """从文件加载RAG"""
        raise NotImplementedError

    # 哈希去重
    def _hash_deduplication(
        self,
        raw_paragraphs: Dict[str, str],
        triple_list_data: Dict[str, List[List[str]]],
    ):
        """段落去重，并将索引换为对应段落的hash值"""
        for idx, raw_paragraph in raw_paragraphs:
            hash_value = hash(raw_paragraph)
            if hash_value in self.stored_paragraph_hashes:
                logger.info(f"删除重复段落，索引：<{idx}>")
                del raw_paragraphs[idx]
                del triple_list_data[idx]
            else:
                self.stored_paragraph_hashes.add(hash_value)
                raw_paragraphs[hash_value] = raw_paragraphs.pop(idx)
                triple_list_data[hash_value] = triple_list_data.pop(idx)

        return raw_paragraphs, triple_list_data

    def _build_edges_between_ent(self, triple_list_data: Dict[str, List[List[str]]]):
        """构建实体节点之间的关系，同时统计实体出现次数"""
        for triple_list in triple_list_data.values():
            entity_set = set()
            for triple in triple_list:
                # 一个triple就是一条边（同时构建双向联系）
                hash_key1 = ENT_NAMESPACE + "-" + str(triple[0])
                hash_key2 = ENT_NAMESPACE + "-" + str(triple[2])
                self.node_to_node[(hash_key1, hash_key2)] = (
                    self.node_to_node.get((hash_key1, hash_key2), 0) + 1.0
                )
                self.node_to_node[(hash_key2, hash_key1)] = (
                    self.node_to_node.get((hash_key2, hash_key1), 0) + 1.0
                )
                entity_set.add(hash_key1)
                entity_set.add(hash_key2)

            # 实体出现次数统计
            for hash_key in entity_set:
                self.ent_appear_cnt[hash_key] = (
                    self.ent_appear_cnt.get(hash_key, 0) + 1.0
                )

    def _build_edges_between_ent_pg(self, triple_list_data: Dict[str, List[List[str]]]):
        """构建实体节点与文段节点之间的关系"""
        for idx, triple_list in triple_list_data:
            for triple in triple_list:
                ent_hash_key = ENT_NAMESPACE + "-" + str(triple[0])
                pg_hash_key = PG_NAMESPACE + "-" + str(idx)
                self.node_to_node[(pg_hash_key, ent_hash_key)] = (
                    self.node_to_node.get((pg_hash_key, ent_hash_key), 0) + 1.0
                )

    def build_rag(
        self,
        openie_obj: OpenIE,
    ):
        """构建RAG"""
        logger.info("开始构建RAG")

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

        # 段落去重，并将索引换为对应段落的hash值
        logger.info("正在进行段落去重与重索引")
        raw_paragraphs, triple_list_data = self._hash_deduplication(
            raw_paragraphs, triple_list_data
        )
        logger.info(f"段落去重完成，剩余待处理的段落数量：{len(raw_paragraphs)}")

        # 构建实体节点之间的关系，同时统计实体出现次数
        logger.info("正在构建RAG实体节点之间的关系，同时统计实体出现次数")
        # 从三元组提取实体对
        self._build_edges_between_ent(triple_list_data)

        # 构建实体节点与文段节点之间的关系
        logger.info("正在构建RAG实体节点与文段节点之间的关系")
        self._build_edges_between_ent_pg(triple_list_data)

        """ 解除注释以启用Embedding库
        logger.info("将段落编码存入Embedding库")
        self.paragraphs_embedding_store.insert_strs(raw_paragraphs)
        logger.info("将实体编码存入Embedding库")
        self.entities_embedding_store.insert_strs(entities)
        logger.info("将关系编码存入Embedding库")
        self.relation_embedding_store.insert_strs([str(triple) for triple in triples])
        """

        # 近义词扩展链接
