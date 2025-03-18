from dataclasses import dataclass
from typing import List

import numpy as np

from config import global_config
from utils import get_md5


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
    def __init__(self, llm_client, namespace: str):
        self.namespace = namespace
        self.llm_client = llm_client
        self.store = dict()

    def _get_embedding(self, s: str) -> List[float]:
        self.llm_client.send_embedding_request(global_config.embed_llm_type, s)

    def insert_strs(self, strs: List[str]) -> None:
        """向库中存入字符串"""

        # 逐项处理
        for s in strs:
            # 计算hash去重
            hash = self.namespace + "-" + get_md5(s)
            if hash in self.store:
                continue

            # 获取embedding
            embedding = self._get_embedding(s)

            # 存入
            self.store[hash] = EmbeddingStoreItem(hash, embedding, s)

    def to_dict(self) -> dict:
        """转为dict"""
        return {
            "namespace": self.namespace,
            "store": [item.to_dict() for item in self.store.values()],
        }
