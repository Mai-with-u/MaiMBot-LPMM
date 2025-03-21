import json
import os
from typing import Dict, List, Tuple

import pandas as pd
import tqdm


from .utils import get_md5
from .embedding_store import EmbeddingManager
from .config import (
    ENT_NAMESPACE,
    PG_NAMESPACE,
    RAG_EDGE_NAMESPACE,
    RAG_ENT_CNT_NAMESPACE,
    RAG_PG_HASH_NAMESPACE,
    global_config,
)

from global_logger import logger


class RAGManager:
    def __init__(self):
        # 存储段落的hash值，用于去重
        self.stored_paragraph_hashes = set()
        # 实体之间的联系
        self.node_to_node = dict()
        # 实体出现次数统计，用于计算权重
        self.ent_appear_cnt = dict()

        self.dir_path = global_config["persistence"]["rag_data_dir"]
        self.edge_file_path = self.dir_path + "/" + RAG_EDGE_NAMESPACE + ".parquet"
        self.ent_appear_file_path = (
            self.dir_path + "/" + RAG_ENT_CNT_NAMESPACE + ".parquet"
        )
        self.pg_hash_file_path = self.dir_path + "/" + RAG_PG_HASH_NAMESPACE + ".json"

    def save_to_file(self):
        """保存到文件"""
        # 保存RAG
        # 确保目录存在
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path, exist_ok=True)
        # 保存RAG边到文件
        open(self.edge_file_path, "w", encoding="utf-8")
        edge_data = []
        for k, v in self.node_to_node.items():
            edge_data.append(
                {"start_hash_key": k[0], "end_hash_key": k[1], "weight": v}
            )
        data_frame = pd.DataFrame(edge_data)
        data_frame.to_parquet(self.edge_file_path, engine="pyarrow", index=False)

        # 保存RAG实体出现计数到文件
        open(self.ent_appear_file_path, "w", encoding="utf-8")
        ent_appear_data = []
        for k, v in self.ent_appear_cnt.items():
            ent_appear_data.append({"hash_key": k, "appear_cnt": v})
        data_frame = pd.DataFrame(ent_appear_data)
        data_frame.to_parquet(self.ent_appear_file_path, engine="pyarrow", index=False)

        # 保存RAG段落hash到文件
        with open(self.pg_hash_file_path, "w", encoding="utf-8") as f:
            data = {"stored_paragraph_hashes": list(self.stored_paragraph_hashes)}
            f.write(json.dumps(data, ensure_ascii=False, indent=4))

    def load_from_file(self):
        """从文件加载"""
        # 加载RAG
        # 确保文件存在
        if not os.path.exists(self.pg_hash_file_path):
            raise Exception(f"RAG段落hash文件{self.pg_hash_file_path}不存在")
        if not os.path.exists(self.ent_appear_file_path):
            raise Exception(f"RAG实体出现次数文件{self.ent_appear_file_path}不存在")
        if not os.path.exists(self.edge_file_path):
            raise Exception(f"RAG边文件{self.edge_file_path}不存在")

        # 加载RAG段落hash
        with open(self.pg_hash_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.stored_paragraph_hashes = set(data["stored_paragraph_hashes"])

        # 加载RAG实体出现次数
        ent_appear_data = pd.read_parquet(self.ent_appear_file_path, engine="pyarrow")
        for _, row in tqdm.tqdm(ent_appear_data.iterrows(), total=len(ent_appear_data)):
            self.ent_appear_cnt[row["hash_key"]] = row["appear_cnt"]

        # 加载RAG边
        edge_data = pd.read_parquet(self.edge_file_path, engine="pyarrow")
        for _, row in tqdm.tqdm(edge_data.iterrows(), total=len(edge_data)):
            self.node_to_node[(row["start_hash_key"], row["end_hash_key"])] = row[
                "weight"
            ]

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

    def _synonym_connect(
        self,
        triple_list_data: Dict[str, List[List[str]]],
        embedding_manager: EmbeddingManager,
    ) -> int:
        """同义词连接"""
        new_edge_cnt = 0
        # 获取所有实体节点的hash值
        ent_hash_list = set()
        for triple_list in triple_list_data.values():
            for triple in triple_list:
                ent_hash_list.add(ENT_NAMESPACE + "-" + get_md5(triple[0]))
                ent_hash_list.add(ENT_NAMESPACE + "-" + get_md5(triple[2]))
        ent_hash_list = list(ent_hash_list)

        synonym_hash_set = set()

        synonym_result = dict()

        # 对每个实体节点，查找其相似的实体节点，建立扩展连接
        for ent_hash in tqdm.tqdm(ent_hash_list):
            if ent_hash in synonym_hash_set:
                # 避免同一批次内重复添加
                continue
            ent = embedding_manager.entities_embedding_store.store.get(ent_hash)
            if ent is None:
                continue
            # 查询相似实体
            similar_ents = embedding_manager.entities_embedding_store.search_top_k(
                ent.embedding, global_config["rag"]["params"]["synonym_search_top_k"]
            )
            res_ent = []  # Debug
            for res_ent_hash, similarity in similar_ents:
                if res_ent_hash == ent_hash:
                    # 避免自连接
                    continue
                if similarity < global_config["rag"]["params"]["synonym_threshold"]:
                    # 相似度阈值
                    continue
                self.node_to_node[(res_ent_hash, ent_hash)] = similarity
                self.node_to_node[(ent_hash, res_ent_hash)] = similarity
                synonym_hash_set.add(res_ent_hash)
                new_edge_cnt += 1
                res_ent.append(
                    (
                        embedding_manager.entities_embedding_store.store[
                            res_ent_hash
                        ].str,
                        similarity,
                    )
                )  # Debug
                synonym_result[ent.str] = res_ent

        for k, v in synonym_result.items():
            print(f'"{k}"的相似实体为：{v}')
        return new_edge_cnt

    def build_rag(
        self,
        triple_list_data: Dict[str, List[List[str]]],
        embedding_manager: EmbeddingManager,
    ):
        """构建RAG"""
        logger.info("开始构建RAG")

        # 记录已处理（存储）的段落hash
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
        # 对每个实体节点，找到最相似的实体节点，建立扩展连接
        logger.info("正在进行近义词扩展链接")
        self._synonym_connect(triple_list_data, embedding_manager)
