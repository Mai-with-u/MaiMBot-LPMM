import json
import os
from typing import Dict, List


from .utils import get_md5
from .embedding_store import EmbeddingManager
from .config import ENT_NAMESPACE, PG_NAMESPACE, global_config

from global_logger import logger


class RAGManager:
    def __init__(self):
        # 存储段落的hash值，用于去重
        self.stored_paragraph_hashes = set()

        # 实体之间的联系
        self.node_to_node = dict()
        # 实体出现次数统计，用于计算权重
        self.ent_appear_cnt = dict()

    def save_to_file(self):
        """保存到文件"""
        # 保存RAG
        # 确保目录存在
        dir_path = global_config["persistence"]["rag_data_path"].rsplit("/", 1)[0]
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(
            global_config["persistence"]["rag_data_path"], "w", encoding="utf-8"
        ) as f:
            rag_data = dict(
                {
                    "stored_paragraph_hashes": list(self.stored_paragraph_hashes),
                    "node_to_node": {
                        f"{k[0]}->{k[1]}": v for k, v in self.node_to_node.items()
                    },
                    "ent_appear_cnt": self.ent_appear_cnt,
                }
            )
            f.write(json.dumps(rag_data))

    def load_from_file(self):
        """从文件加载"""
        # 加载RAG
        if not os.path.exists(global_config["persistence"]["rag_data_file"]):
            raise Exception(
                f"文件{global_config['persistence']['rag_data_file']}不存在"
            )
        with open(
            global_config["persistence"]["rag_data_file"], "r", encoding="utf-8"
        ) as f:
            rag_data = json.load(f)

        self.stored_paragraph_hashes = set(rag_data["stored_paragraph_hashes"])
        self.node_to_node = dict()
        for k, v in rag_data["node_to_node"].items():
            self.node_to_node[tuple(k.split("->"))] = v
        self.ent_appear_cnt = rag_data["ent_appear_cnt"]

    def _build_edges_between_ent(self, triple_list_data: Dict[str, List[List[str]]]):
        """构建实体节点之间的关系，同时统计实体出现次数"""
        for triple_list in triple_list_data.values():
            entity_set = set()
            for triple in triple_list:
                # 一个triple就是一条边（同时构建双向联系）
                hash_key1 = ENT_NAMESPACE + "-" + get_md5(triple[0])
                hash_key2 = ENT_NAMESPACE + "-" + get_md5(triple[2])
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
        for idx in triple_list_data:
            for triple in triple_list_data[idx]:
                ent_hash_key = ENT_NAMESPACE + "-" + get_md5(triple[0])
                pg_hash_key = PG_NAMESPACE + "-" + str(idx)
                self.node_to_node[(pg_hash_key, ent_hash_key)] = (
                    self.node_to_node.get((pg_hash_key, ent_hash_key), 0) + 1.0
                )

    def build_rag(
        self,
        triple_list_data: Dict[str, List[List[str]]],
        embedding_manager: EmbeddingManager,
    ):
        """构建RAG"""
        logger.info("开始构建RAG")

        for idx in triple_list_data:
            self.stored_paragraph_hashes.add(str(idx))

        # 构建实体节点之间的关系，同时统计实体出现次数
        logger.info("正在构建RAG实体节点之间的关系，同时统计实体出现次数")
        # 从三元组提取实体对
        self._build_edges_between_ent(triple_list_data)

        # 构建实体节点与文段节点之间的关系
        logger.info("正在构建RAG实体节点与文段节点之间的关系")
        self._build_edges_between_ent_pg(triple_list_data)

        # 近义词扩展链接
        logger.info("正在进行近义词扩展链接")
        # 对每个实体节点，找到最相似的实体节点，建立扩展连接
