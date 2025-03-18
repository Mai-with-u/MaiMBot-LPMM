from dataclasses import dataclass
import json
from typing import Any, Dict, List

import numpy as np
from config import global_config


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
        with open(global_config.openie_file, "w", encoding="utf-8") as f:
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
            {doc_item["idx"]: doc_item["raw_paragraph"] for doc_item in self.docs}
        )
        return raw_paragraph_dict
