import json
import os
from typing import Any, Dict, List


from .llm_client import LLMClient
from .config import global_config
from global_logger import logger
from .entity_processing import process_entity_extract
from .raw_processing import load_raw_data
from .rdf_processing import process_rdf_extract


def filter_invalid_triples(triples: List[List[str]]) -> List[List[str]]:
    """过滤无效的三元组"""
    unique_triples = set()
    valid_triples = []

    for triple in triples:
        if len(triple) != 3:
            continue  #

        valid_triple = [str(item) for item in triple]
        if tuple(valid_triple) not in unique_triples:
            unique_triples.add(tuple(valid_triple))
            valid_triples.append(valid_triple)

    return valid_triples


class OpenIE:
    def __init__(
        self,
        docs: List[Dict[str, Any]],
        avg_ent_chars,
        avg_ent_words,
    ):
        self.docs = docs
        self.avg_ent_chars = avg_ent_chars
        self.avg_ent_words = avg_ent_words

    def from_all_docs(all_docs: List[Dict[str, Any]]) -> "OpenIE":
        """从完整文档中获取OpenIE对象"""
        docs = all_docs

        sum_phrase_chars = sum(
            [len(e) for chunk in docs for e in chunk["extracted_entities"]]
        )
        sum_phrase_words = sum(
            [len(e.split()) for chunk in docs for e in chunk["extracted_entities"]]
        )
        num_phrases = sum([len(chunk["extracted_entities"]) for chunk in docs])

        avg_ent_chars = round(sum_phrase_chars / num_phrases, 4)
        avg_ent_words = round(sum_phrase_words / num_phrases, 4)

        return OpenIE(docs, avg_ent_chars, avg_ent_words)

    def from_dict(data):
        """从字典中获取OpenIE对象"""
        return OpenIE(
            docs=data["docs"],
            avg_ent_chars=data["avg_ent_chars"],
            avg_ent_words=data["avg_ent_words"],
        )

    def to_dict(self):
        return {
            "docs": self.docs,
            "avg_ent_chars": self.avg_ent_chars,
            "avg_ent_words": self.avg_ent_words,
        }

    def save_data_as_openie_format(self):
        """将数据保存为OpenIE格式"""
        with open(
            global_config["persistence"]["openie_data_path"], "w", encoding="utf-8"
        ) as f:
            f.write(json.dumps(self.to_dict(), ensure_ascii=False))

    def extract_entity_dict(self):
        """提取实体列表"""
        ner_output_dict = dict(
            {doc_item["idx"]: doc_item["extracted_entities"] for doc_item in self.docs}
        )
        return ner_output_dict

    def extract_triple_dict(self):
        """提取三元组列表"""
        triple_output_dict = dict(
            {doc_item["idx"]: doc_item["extracted_triples"] for doc_item in self.docs}
        )
        return triple_output_dict

    def extract_raw_paragraph_dict(self):
        """提取原始段落"""
        raw_paragraph_dict = dict(
            {doc_item["idx"]: doc_item["passage"] for doc_item in self.docs}
        )
        return raw_paragraph_dict


def get_openie_obj(llm_client_list: Dict[str, LLMClient]) -> OpenIE:
    """获取OpenIE对象"""
    openie_obj = None
    # 检查OpenIE文件是否存在
    if os.path.exists(global_config["persistence"]["openie_data_path"]):
        try:
            with open(
                global_config["persistence"]["openie_data_path"], "r", encoding="utf-8"
            ) as f:
                openie_obj = json.loads(f.read())
            openie_obj = OpenIE.from_dict(openie_obj)
        except Exception as e:
            logger.error("OpenIE文件存在错误：{}".format(e))
            openie_obj = None

    if openie_obj is not None:
        logger.info("OpenIE文件已存在，跳过实体提取、RDF提取任务")
    else:
        logger.info(
            "OpenIE文件为空/不存在/格式错误，开始执行实体提取、RDF提取"
        )

        # 加载import.json文件
        raw_data, md5_set = load_raw_data()

        # 加载实体提取结果
        entities_json = process_entity_extract(
            llm_client_list[global_config["entity_extract"]["llm"]["provider"]],
            raw_data,
            md5_set,
        )

        # 加载RDF结果
        rdf_json = process_rdf_extract(
            llm_client_list[global_config["rdf_build"]["llm"]["provider"]],
            raw_data,
            md5_set,
            entities_json,
        )

        # 转换并保存为OpenIE样式
        logger.info("正在将数据保存为OpenIE格式")
        openie_docs = []
        for item in raw_data:
            if item in entities_json and item in rdf_json:
                openie_docs.append(
                    {
                        "idx": item,
                        "passage": raw_data[item],
                        "extracted_entities": entities_json[item],
                        "extracted_triples": rdf_json[item],
                    }
                )
        openie_obj = OpenIE.from_all_docs(openie_docs)
        openie_obj.save_data_as_openie_format()
        logger.info("OpenIE文件保存成功")

    return openie_obj
