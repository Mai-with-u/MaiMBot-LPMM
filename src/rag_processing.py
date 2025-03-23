import json
import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import tqdm
import igraph as ig


from .utils import get_md5
from .embedding_store import EmbeddingManager, EmbeddingStoreItem
from .config import (
    ENT_NAMESPACE,
    PG_NAMESPACE,
    RAG_ENT_CNT_NAMESPACE,
    RAG_GRAPH_NAMESPACE,
    RAG_PG_HASH_NAMESPACE,
    global_config,
)

from global_logger import logger


class RAGManager:
    def __init__(self):
        # 存储段落的hash值，用于去重
        self.stored_paragraph_hashes = set()
        # 实体出现次数
        self.ent_appear_cnt = dict()
        # RAG图
        self.graph = ig.Graph(directed=True)

        # 图结构索引&映射
        # 从node-key到图中的索引
        self.igraph_name2idx: Dict[str, int] = dict()

        # 持久化相关
        self.dir_path = global_config["persistence"]["rag_data_dir"]
        self.graph_data_path = self.dir_path + "/" + RAG_GRAPH_NAMESPACE + ".gml"
        self.ent_cnt_data_path = (
            self.dir_path + "/" + RAG_ENT_CNT_NAMESPACE + ".parquet"
        )
        self.pg_hash_file_path = self.dir_path + "/" + RAG_PG_HASH_NAMESPACE + ".json"

    def save_to_file(self):
        """将RAG数据保存到文件"""
        # 保存RAG
        # 确保目录存在
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path, exist_ok=True)

        # 保存RAG图到文件
        if isinstance(self.graph, ig.Graph):
            self.graph.write(self.graph_data_path, format="gml")

        # 保存实体计数到文件
        ent_cnt_df = pd.DataFrame(
            [{"hash_key": k, "appear_cnt": v} for k, v in self.ent_appear_cnt.items()]
        )
        ent_cnt_df.to_parquet(self.ent_cnt_data_path, engine="pyarrow", index=False)

        # 保存RAG段落hash到文件
        with open(self.pg_hash_file_path, "w", encoding="utf-8") as f:
            data = {"stored_paragraph_hashes": list(self.stored_paragraph_hashes)}
            f.write(json.dumps(data, ensure_ascii=False, indent=4))

    def load_from_file(self):
        """从文件加载RAG数据"""
        # 加载RAG
        # 确保文件存在
        if not os.path.exists(self.pg_hash_file_path):
            raise Exception(f"RAG段落hash文件{self.pg_hash_file_path}不存在")
        if not os.path.exists(self.ent_cnt_data_path):
            raise Exception(f"RAG实体计数文件{self.ent_cnt_data_path}不存在")
        if not os.path.exists(self.graph_data_path):
            raise Exception(f"RAG图文件{self.graph_data_path}不存在")

        # 加载RAG段落hash
        with open(self.pg_hash_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.stored_paragraph_hashes = set(data["stored_paragraph_hashes"])

        # 加载RAG实体计数
        ent_cnt_df = pd.read_parquet(self.ent_cnt_data_path, engine="pyarrow")
        self.ent_appear_cnt = dict(
            {row["hash_key"]: row["appear_cnt"] for _, row in ent_cnt_df.iterrows()}
        )

        # 加载RAG图
        self.graph = ig.Graph.Read(self.graph_data_path, format="gml")
        self.igraph_name2idx = {
            node["name"]: idx for idx, node in enumerate(self.graph.vs)
        }

    def _build_edges_between_ent(
        self,
        node_to_node: Dict[Tuple[str, str], float],
        triple_list_data: Dict[str, List[List[str]]],
    ):
        """构建实体节点之间的关系，同时统计实体出现次数"""
        for triple_list in triple_list_data.values():
            entity_set = set()
            for triple in triple_list:
                # 一个triple就是一条边（同时构建双向联系）
                hash_key1 = ENT_NAMESPACE + "-" + get_md5(triple[0])
                hash_key2 = ENT_NAMESPACE + "-" + get_md5(triple[2])
                node_to_node[(hash_key1, hash_key2)] = (
                    node_to_node.get((hash_key1, hash_key2), 0) + 1.0
                )
                node_to_node[(hash_key2, hash_key1)] = (
                    node_to_node.get((hash_key2, hash_key1), 0) + 1.0
                )
                entity_set.add(hash_key1)
                entity_set.add(hash_key2)

            # 实体出现次数统计
            for hash_key in entity_set:
                self.ent_appear_cnt[hash_key] = (
                    self.ent_appear_cnt.get(hash_key, 0) + 1.0
                )

    def _build_edges_between_ent_pg(
        self,
        node_to_node: Dict[Tuple[str, str], float],
        triple_list_data: Dict[str, List[List[str]]],
    ):
        """构建实体节点与文段节点之间的关系"""
        for idx in triple_list_data:
            for triple in triple_list_data[idx]:
                ent_hash_key = ENT_NAMESPACE + "-" + get_md5(triple[0])
                pg_hash_key = PG_NAMESPACE + "-" + str(idx)
                node_to_node[(ent_hash_key, pg_hash_key)] = (
                    node_to_node.get((ent_hash_key, pg_hash_key), 0) + 1.0
                )

    def _synonym_connect(
        self,
        node_to_node: Dict[Tuple[str, str], float],
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
            assert isinstance(ent, EmbeddingStoreItem)
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
                node_to_node[(res_ent_hash, ent_hash)] = similarity
                node_to_node[(ent_hash, res_ent_hash)] = similarity
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

    def _add_nodes(
        self,
        node_to_node: Dict[Tuple[str, str], float],
    ):
        """向Graph添加节点"""
        # TODO: 需要测试-在已有节点的情况下，是否会重复添加节点
        # 已存在的节点
        existing_nodes = {
            v["name"]: v for v in self.graph.vs if "name" in v.attributes()
        }

        # 筛出新节点
        new_node_attrs = {"name": [], "type": []}
        for key in node_to_node:
            for node_hash in key:
                if (node_hash not in existing_nodes) and (
                    node_hash not in new_node_attrs["name"]
                ):
                    # 既不是已存在节点，也不是已记录的新节点
                    new_node_attrs["name"].append(node_hash)
                    if node_hash.startswith(ENT_NAMESPACE):
                        new_node_attrs["type"].append("ent")
                    elif node_hash.startswith(PG_NAMESPACE):
                        new_node_attrs["type"].append("pg")
                    else:
                        raise Exception(f"未知节点类型：{node_hash}")

        self.graph.add_vertices(
            n=len(new_node_attrs["name"]), attributes=new_node_attrs
        )

    def _add_edges(
        self,
        node_to_node: Dict[Tuple[str, str], float],
    ):
        """向Graph添加边"""
        # TODO: 需要测试-在已有边的情况下，是否会重复添加边
        # 已存在的边
        existing_edges = {
            (v.source, v.target): v for v in self.graph.es if "weight" in v.attributes()
        }

        # 遍历所有新边
        edge_to_add, edge_to_add_attrs = [], dict({"weight": []})
        for key, weight in node_to_node.items():
            if key not in existing_edges:
                # 未记录的边
                edge_to_add.append(key)
                edge_to_add_attrs["weight"].append(weight)
            else:
                # 已记录的边
                existing_edges[key]["weight"] += weight

        # 添加新边
        self.graph.add_edges(edge_to_add, attributes=edge_to_add_attrs)

    def build_rag(
        self,
        triple_list_data: Dict[str, List[List[str]]],
        embedding_manager: EmbeddingManager,
    ):
        """增量式构建RAG

        注意：应当在调用该方法后保存RAG

        Args:
            triple_list_data: 三元组数据
            embedding_manager: EmbeddingManager对象
        """
        logger.info("开始构建RAG")

        # 实体之间的联系
        node_to_node = dict()

        # 记录已处理（存储）的段落hash
        for idx in triple_list_data:
            self.stored_paragraph_hashes.add(str(idx))

        # 构建实体节点之间的关系，同时统计实体出现次数
        logger.info("正在构建RAG实体节点之间的关系，同时统计实体出现次数")
        # 从三元组提取实体对
        self._build_edges_between_ent(node_to_node, triple_list_data)

        # 构建实体节点与文段节点之间的关系
        logger.info("正在构建RAG实体节点与文段节点之间的关系")
        self._build_edges_between_ent_pg(node_to_node, triple_list_data)

        # 近义词扩展链接
        # 对每个实体节点，找到最相似的实体节点，建立扩展连接
        logger.info("正在进行近义词扩展链接")
        self._synonym_connect(node_to_node, triple_list_data, embedding_manager)

        # 构建图
        # sync_igraph
        # 从node_to_node中提取节点和边
        self._add_nodes(node_to_node)
        self._add_edges(node_to_node)
        # 更新索引映射
        self.igraph_name2idx = {
            node["name"]: idx for idx, node in enumerate(self.graph.vs)
        }

    def rag_search_and_pr(
        self,
        relation_search_result: List[Tuple[Tuple[str, str, str], float]],
        paragraph_search_result: List[Tuple[str, float]],
    ):
        """RAG搜索与PageRank

        Args:
            relation_search_result: RelationEmbedding的搜索结果（relation_tripple, similarity）
            paragraph_search_result: ParagraphEmbedding的搜索结果（paragraph_hash, similarity）
        """
        logger.info("开始RAG搜索")

        # 准备PPR使用的数据
        # 节点权重：实体
        ent_weights = np.zeros(len(self.graph.vs["name"]))
        # 节点权重：文段
        pg_weights = np.zeros(len(self.graph.vs["name"]))

        # 以下部分处理实体权重

        # 针对每个关系，提取出其中的主宾短语作为两个实体，并记录对应的三元组的相似度作为权重依据
        ent_sim_scores = {}
        for relation, similarity in relation_search_result:
            # 提取主宾短语
            subject = relation[0]
            object = relation[2]
            for ent in [subject, object]:
                hash_key = ENT_NAMESPACE + "-" + get_md5(ent)
                if hash_key in self.igraph_name2idx:
                    # 该实体需在RAG中出现过，没出现过的实体不计算权重
                    if hash_key not in ent_sim_scores:
                        ent_sim_scores[hash_key] = (ent, [])
                    ent_sim_scores[hash_key][1].append(similarity)

        ent_scores = {}  # 记录实体的平均相似度
        for hash_key, item in ent_sim_scores.items():
            idx = self.igraph_name2idx[hash_key]
            ent = item[0]
            scores = item[1]
            # 先对相似度进行累加，然后与实体计数相除获取最终权重
            ent_weights[idx] = np.sum(scores) / self.ent_appear_cnt[hash_key]
            # 记录实体的平均相似度，用于后续的top_k筛选
            ent_scores[idx] = float(np.mean(scores))
        del ent_sim_scores

        # 取平均相似度的top_k实体
        top_k = global_config["qa"]["params"]["ent_filter_top_k"]
        if len(ent_scores) > top_k:
            # 从大到小排序，取后len - k个
            ent_scores = dict(
                sorted(ent_scores.items(), key=lambda x: x[1], reverse=True)[top_k:]
            )
            for idx, _ in ent_scores.items():
                # 将被淘汰的实体节点权重置为0
                ent_weights[idx] = 0
        assert np.count_nonzero(ent_weights) == len(
            ent_scores.keys()
        )  # 断言：权重非零的实体节点数量应与top_k相等
        del top_k, ent_scores

        # 以下部分处理文段权重

        # 将搜索结果中文段的相似度归一化作为权重
        pg_sim_scores = []
        pg_idxs = []
        pg_sim_score_max = 1.0
        pg_sim_score_min = 0.0
        for pg_hash, similarity in paragraph_search_result:
            # 查找最大和最小值
            pg_sim_score_max = max(pg_sim_score_max, similarity)
            pg_sim_score_min = min(pg_sim_score_min, similarity)
            pg_sim_scores.append(similarity)
            pg_idxs.append(self.igraph_name2idx[pg_hash])

        # 归一化
        pg_sim_scores = np.array(pg_sim_scores)
        pg_sim_scores = (pg_sim_scores - pg_sim_score_min) / (
            pg_sim_score_max - pg_sim_score_min
        )
        del pg_sim_score_max, pg_sim_score_min

        for pg_idx, score in zip(pg_idxs, pg_sim_scores):
            pg_weights[pg_idx] = (
                score * global_config["qa"]["params"]["paragraph_node_weight"]
            )  # 文段权重 = 归一化相似度 * 文段节点权重参数

        # 最终权重数据 = 实体权重 + 文段权重
        node_weights = ent_weights + pg_weights

        # PersonalizedPageRank
        reset_prob = np.where(
            np.isnan(node_weights) | (node_weights < 0), 0, node_weights
        )
        pagerank_scores = self.graph.personalized_pagerank(
            vertices=range(len(self.igraph_name2idx)),
            damping=global_config["qa"]["params"]["ppr_damping"],
            directed=False,
            weights="weight",
            reset=reset_prob,
            implementation="prpack",
        )

        # 获取最终结果
        # 从搜索结果中提取文段节点的结果
        passage_node_idxs = [
            self.igraph_name2idx[PG_NAMESPACE + "-" + pg_hash]
            for pg_hash in self.stored_paragraph_hashes
        ]
        passage_node_res = [(idx, pagerank_scores[idx]) for idx in passage_node_idxs]

        # 排序：按照分数从大到小
        passage_node_res = sorted(passage_node_res, key=lambda x: x[1], reverse=True)

        # 获取文段哈希键
        sorted_doc_hashes = [
            self.graph.vs[idx]["name"] for (idx, _) in passage_node_res
        ]

        # 转换为文段哈希键和分数的列表
        res = [
            (hash_key, score[1])
            for hash_key, score in zip(sorted_doc_hashes, passage_node_res)
        ]

        return res
