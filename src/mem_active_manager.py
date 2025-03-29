from src.config import global_config
from src.embedding_store import EmbeddingManager
from src.llm_client import LLMClient
from src.utils.dyn_topk import dyn_select_top_k


class MemActiveManager:
    def __init__(
        self,
        embed_manager: EmbeddingManager,
        llm_client_embedding: LLMClient,
    ):
        self.embed_manager = embed_manager
        self.embedding_client = llm_client_embedding

    def get_activation(self, question: str) -> float:
        """获取激活度"""
        # 生成问题的Embedding
        question_embedding = self.embedding_client.send_embedding_request(
            "text-embedding", question
        )
        # 查询关系库中的相似度
        rel_res = self.embed_manager.relation_embedding_store.search_top_k(
            question_embedding, 10
        )

        # 动态过滤阈值
        rel_score = dyn_select_top_k(rel_res, 0.5, 1.0)
        if rel_score[0][1] < global_config["qa"]["params"]["relation_threshold"]:
            # 未找到相关关系
            return 0.0

        # 计算激活度
        activation = sum(rel_score) * 10

        return activation
