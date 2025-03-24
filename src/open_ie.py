import json
from typing import Any, Dict, List



from .config import global_config


def filter_invalid_triples(triples: List[List[str]]) -> List[List[str]]:
    """过滤无效的三元组"""
    unique_triples = set()
    valid_triples = []

    for triple in triples:
        if len(triple) != 3 or (
            (triple[0] is None or triple[0].strip() == "")
            or (triple[1] is None or triple[1].strip() == "")
            or (triple[2] is None or triple[2].strip() == "")
        ):
            # 三元组长度不为3，或其中存在空值
            continue

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

    def _from_dict(data):
        """从字典中获取OpenIE对象"""
        return OpenIE(
            docs=data["docs"],
            avg_ent_chars=data["avg_ent_chars"],
            avg_ent_words=data["avg_ent_words"],
        )

    def _to_dict(self):
        """转换为字典"""
        return {
            "docs": self.docs,
            "avg_ent_chars": self.avg_ent_chars,
            "avg_ent_words": self.avg_ent_words,
        }

    def load_from_file() -> "OpenIE":
        """从文件中加载OpenIE数据"""
        with open(
            global_config["persistence"]["openie_data_path"], "r", encoding="utf-8"
        ) as f:
            data = json.loads(f.read())

        openie_data = OpenIE._from_dict(data)

        return openie_data

    def save_to_file(self):
        """保存OpenIE数据到文件"""
        with open(
            global_config["persistence"]["openie_data_path"], "w", encoding="utf-8"
        ) as f:
            f.write(json.dumps(self._to_dict(), ensure_ascii=False, indent=4))

    def extract_entity_dict(self):
        """提取实体列表"""
        ner_output_dict = dict(
            {
                doc_item["idx"]: doc_item["extracted_entities"]
                for doc_item in self.docs
                if len(doc_item["extracted_entities"]) > 0
            }
        )
        return ner_output_dict

    def extract_triple_dict(self):
        """提取三元组列表"""
        triple_output_dict = dict(
            {
                doc_item["idx"]: doc_item["extracted_triples"]
                for doc_item in self.docs
                if len(doc_item["extracted_triples"]) > 0
            }
        )
        return triple_output_dict

    def extract_raw_paragraph_dict(self):
        """提取原始段落"""
        raw_paragraph_dict = dict(
            {doc_item["idx"]: doc_item["passage"] for doc_item in self.docs}
        )
        return raw_paragraph_dict
