import os
import toml
import argparse

PG_NAMESPACE = "paragraph"
ENT_NAMESPACE = "entity"
REL_NAMESPACE = "relation"


def _load_config(config, config_file_path):
    """读取TOML格式的配置文件"""
    if not os.path.exists(config_file_path):
        return
    with open(config_file_path, "r", encoding="utf-8") as f:
        file_config = toml.load(f)

    if "llm_providers" in file_config:
        for provider in file_config["llm_providers"]:
            config["llm_providers"][provider["name"]]["base_url"] = provider["base_url"]
            config["llm_providers"][provider["name"]]["api_key"] = provider["api_key"]

    if "entity_extract" in file_config:
        config["entity_extract"] = file_config["entity_extract"]

    if "rdf_build" in file_config:
        config["rdf_build"] = file_config["rdf_build"]

    if "embedding" in file_config:
        config["embedding"] = file_config["embedding"]

    if "rag" in file_config:
        config["rag"] = file_config["rag"]

    if "persistence" in file_config:
        config["persistence"] = file_config["persistence"]

    print("Configurations loaded from file: ", config_file_path)
    print(config)


parser = argparse.ArgumentParser(description="Configurations for the pipeline")
parser.add_argument(
    "--config_path",
    type=str,
    default="config.toml",
    help="Path to the configuration file",
)

global_config = dict(
    {
        "llm_providers": {
            "localhost": {
                "base_url": "http://localhost:8000",
                "api_key": "",
            }
        },
        "entity_extract": {
            "llm": {
                "provider": "localhost",
                "model": "entity-extract",
            }
        },
        "rdf_build": {
            "llm": {
                "provider": "localhost",
                "model": "rdf-build",
            }
        },
        "embedding": {
            "provider": "localhost",
            "model": "embed",
        },
        "rag": {
            "params": {
                "synonym_search_top_k": 10,
                "synonym_threshold": 0.8,
            }
        },
        "persistence": {
            "raw_data_path": "data/raw.json",
            "entity_data_path": "data/entity.json",
            "rdf_data_path": "data/rdf.json",
            "openie_data_path": "data/openie.json",
            "embedding_data_dir": "data/embedding",
            "rag_data_file": "data/rag.json",
            "embed_index_path": "data/embedding/embedding.index",
        },
    }
)

_load_config(global_config, parser.parse_args().config_path)
