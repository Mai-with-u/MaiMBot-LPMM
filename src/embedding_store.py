from dataclasses import dataclass
import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import tqdm
import faiss

from .llm_client import LLMClient
from .config import ENT_NAMESPACE, PG_NAMESPACE, REL_NAMESPACE, global_config
from .utils import get_md5
from global_logger import logger


@dataclass
class EmbeddingStoreItem:
    """嵌入库中的项"""

    def __init__(self, hash: str, embedding: List[float], str: str):
        self.hash = hash
        self.embedding = embedding
        self.str = str

    def cosine_compare(
        item1: "EmbeddingStoreItem", item2: "EmbeddingStoreItem"
    ) -> float:
        """比较两个项的Embedding的余弦相似度"""
        embed1 = np.array(item1.embedding)
        embed2 = np.array(item2.embedding)
        assert len(embed1) == len(embed2), "两个Embedding长度不一致"
        cosine = np.dot(embed1, embed2) / (
            np.linalg.norm(embed1) * np.linalg.norm(embed2)
        )
        return cosine

    def to_dict(self) -> dict:
        """转为dict"""
        return {
            "hash": self.hash,
            "embedding": self.embedding,
            "str": self.str,
        }


class EmbeddingStore:
    def __init__(self, llm_client: LLMClient, namespace: str, dir_path: str):
        self.namespace = namespace
        self.llm_client = llm_client
        self.dir = dir_path
        self.file_path = dir_path + "/" + namespace + ".parquet"

        self.store = dict()

        self.faiss_index = None
        self.idx2hash = None

    def _get_embedding(self, s: str) -> List[float]:
        return self.llm_client.send_embedding_request(
            global_config["embedding"]["model"], s
        )

    def batch_insert_strs(self, strs: List[str]) -> None:
        """向库中存入字符串"""
        # 逐项处理
        for s in tqdm.tqdm(strs):
            # 计算hash去重
            hash = self.namespace + "-" + get_md5(s)
            if hash in self.store:
                continue

            # 获取embedding
            embedding = self._get_embedding(s)

            # 存入
            self.store[hash] = EmbeddingStoreItem(hash, embedding, s)

    def save_to_file(self) -> None:
        """保存到文件"""
        data = []
        logger.info(f"正在保存{self.namespace}嵌入库到文件{self.file_path}")
        for item in self.store.values():
            data.append(item.to_dict())
        data_frame = pd.DataFrame(data)

        if not os.path.exists(self.dir):
            os.makedirs(self.dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            open(self.file_path, "w").close()

        data_frame.to_parquet(self.file_path, engine="pyarrow", index=False)
        logger.info(f"{self.namespace}嵌入库保存成功")

    def load_from_file(self) -> None:
        """从文件中加载"""
        if not os.path.exists(self.file_path):
            raise Exception(f"文件{self.file_path}不存在")

        logger.info(f"正在从文件{self.file_path}中加载{self.namespace}嵌入库")
        data_frame = pd.read_parquet(self.file_path, engine="pyarrow")
        for _, row in tqdm.tqdm(data_frame.iterrows(), total=len(data_frame)):
            self.store[row["hash"]] = EmbeddingStoreItem(
                row["hash"], row["embedding"], row["str"]
            )
        logger.info(f"{self.namespace}嵌入库加载成功")

    def build_faiss_index(self) -> None:
        """重新构建Faiss索引，以余弦相似度为度量"""
        # 获取所有的embedding
        array = []
        self.idx2hash = dict()
        for key in self.store:
            array.append(self.store[key].embedding)
            self.idx2hash[len(array) - 1] = key
        embeddings = np.array(array, dtype=np.float32)
        # L2归一化
        faiss.normalize_L2(embeddings)
        # 构建索引
        self.faiss_index = faiss.IndexFlatIP(global_config["embedding"]["dimension"])
        self.faiss_index.add(embeddings)

    def search_top_k(self, query: List[float], k: int) -> List[Tuple[str, float]]:
        """搜索最相似的k个项，以余弦相似度为度量
        Args:
            query: 查询的embedding
            k: 返回的最相似的k个项
        Returns:
            result: 最相似的k个项的(hash, 余弦相似度)列表
        """
        if self.faiss_index is None:
            raise Exception("Faiss索引尚未构建")
        if self.idx2hash is None:
            raise Exception("idx2hash映射尚未构建")

        # L2归一化
        faiss.normalize_L2(np.array([query], dtype=np.float32))
        # 搜索
        distances, indices = self.faiss_index.search(np.array([query]), k)
        # 整理结果
        indices = indices.flatten()
        distances = distances.flatten()
        result = []
        for i in range(len(indices)):
            result.append((self.idx2hash[indices[i]], distances[i]))

        return result


class EmbeddingManager:
    def __init__(self, llm_client: LLMClient):
        self.paragraphs_embedding_store = EmbeddingStore(
            llm_client,
            PG_NAMESPACE,
            global_config["persistence"]["embedding_data_dir"],
        )
        self.entities_embedding_store = EmbeddingStore(
            llm_client,
            ENT_NAMESPACE,
            global_config["persistence"]["embedding_data_dir"],
        )
        self.relation_embedding_store = EmbeddingStore(
            llm_client,
            REL_NAMESPACE,
            global_config["persistence"]["embedding_data_dir"],
        )
        self.stored_pg_hashes = set()

    def store_pg_into_embedding(self, raw_paragraphs: Dict[str, str]):
        """将段落编码存入Embedding库"""
        self.paragraphs_embedding_store.batch_insert_strs(raw_paragraphs.values())

    def store_ent_into_embedding(self, triple_list_data: Dict[str, List[List[str]]]):
        """将实体编码存入Embedding库"""
        entities = set()
        for triple_list in triple_list_data.values():
            for triple in triple_list:
                entities.add(triple[0])
                entities.add(triple[2])
        self.entities_embedding_store.batch_insert_strs(list(entities))

    def store_rel_into_embedding(self, triple_list_data: Dict[str, List[List[str]]]):
        """将关系编码存入Embedding库"""
        graph_triples = []  # a list of unique relation triple (in tuple) from all chunks
        for triples in triple_list_data.values():
            graph_triples.extend([tuple(t) for t in triples])
        graph_triples = list(set(graph_triples))
        self.relation_embedding_store.batch_insert_strs(
            [str(triple) for triple in graph_triples]
        )

    def load_from_file(self):
        """从文件加载"""
        self.paragraphs_embedding_store.load_from_file()
        self.entities_embedding_store.load_from_file()
        self.relation_embedding_store.load_from_file()
        # 从段落库中获取已存储的hash
        self.stored_pg_hashes = set(self.paragraphs_embedding_store.store.keys())

    def save_to_file(self):
        """保存到文件"""
        self.paragraphs_embedding_store.save_to_file()
        self.entities_embedding_store.save_to_file()
        self.relation_embedding_store.save_to_file()
