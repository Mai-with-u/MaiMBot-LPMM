from global_logger import logger
from src.entity_processing import process_entity_extract
from src.llm_client import LLMClient
from src.open_ie import OpenIE
from src.raw_processing import load_raw_data
from src.config import global_config
from src.rdf_processing import process_rdf_extract


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
    raw_data, sha256_set = load_raw_data()
    logger.info("原始数据加载完成\n")

    logger.info("正在进行信息提取")
    logger.info("正在进行实体列表提取")
    entity_lists = process_entity_extract(
        llm_client_list[global_config["entity_extract"]["llm"]["provider"]],
        raw_data,
        sha256_set,
    )
    logger.info("实体列表提取完成\n")

    logger.info("正在进行关系提取")
    rdf_triple_lists = process_rdf_extract(
        llm_client_list[global_config["rdf_build"]["llm"]["provider"]],
        raw_data,
        sha256_set,
        entity_lists,
    )

    open_ie_doc = []
    for hash in sha256_set:
        open_ie_doc.append(
            {
                "idx": hash,
                "passage": raw_data[hash],
                "extracted_entities": entity_lists[hash],
                "extracted_triples": rdf_triple_lists[hash],
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


if __name__ == "__main__":
    main()
