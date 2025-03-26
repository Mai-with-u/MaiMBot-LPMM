import argparse

import tqdm

from global_logger import logger
from src.config import global_config
from src.ie_process import info_extract_from_str
from src.llm_client import LLMClient
from src.open_ie import OpenIE
from src.raw_processing import load_raw_data


def main():
    logger.info("--------进行信息提取--------\n")

    logger.info("创建LLM客户端")
    llm_client_list = dict()
    for key in global_config["llm_providers"]:
        llm_client_list[key] = LLMClient(
            global_config["llm_providers"][key]["base_url"],
            global_config["llm_providers"][key]["api_key"],
        )

    logger.info("正在加载原始数据")
    sha256_list, raw_datas = load_raw_data()
    logger.info("原始数据加载完成\n")

    entity_lists = []
    rdf_triple_lists = []
    failed_sha256 = []

    for sha, raw_data in tqdm.tqdm(zip(sha256_list, raw_datas), postfix="正在进行提取：", total=len(sha256_list)):
        entity_list, rdf_triple_list = info_extract_from_str(
            llm_client_list[global_config["entity_extract"]["llm"]["provider"]],
            llm_client_list[global_config["rdf_build"]["llm"]["provider"]],
            raw_data,
        )
        if entity_list is None or rdf_triple_list is None:
            failed_sha256.append(sha)
            logger.error(f"提取失败：{sha}")
            continue
        else:
            entity_lists.append(entity_list)
            rdf_triple_lists.append(rdf_triple_list)

    open_ie_doc = []
    for pg_hash, raw_data, entity_list, rdf_triple_list in zip(sha256_list, raw_datas, entity_lists, rdf_triple_lists):
        open_ie_doc.append(
            {
                "idx": pg_hash,
                "passage": raw_data,
                "extracted_entities": entity_list,
                "extracted_triples": rdf_triple_list,
            }
        )

    sum_phrase_chars = sum(
        [len(e) for chunk in open_ie_doc for e in chunk["extracted_entities"]]
    )
    sum_phrase_words = sum(
        [len(e.split()) for chunk in open_ie_doc for e in chunk["extracted_entities"]]
    )
    num_phrases = sum([len(chunk["extracted_entities"]) for chunk in open_ie_doc])

    openie_obj = OpenIE(
        open_ie_doc,
        round(sum_phrase_chars / num_phrases, 4),
        round(sum_phrase_words / num_phrases, 4),
    )

    OpenIE.save(openie_obj)

    logger.info("--------信息提取完成--------")
    logger.info(f"提取失败的文段SHA256：{failed_sha256}")


if __name__ == "__main__":
    main()
