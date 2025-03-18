import argparse


class Config:
    def __init__(
        self,
        llm_base_url,
        entity_extract_llm_type,
        entity_extract_llm_key,
        rdf_build_llm_type,
        rdf_build_llm_key,
        embed_llm_type,
        embed_llm_key,
        entity_file,
        rdf_file,
        openie_file,
        rag_file,
        import_file,
        extract_entities,
        build_rdf,
        build_rag,
        qa_llm_type,
        qa_llm_key,
    ):
        self.llm_base_url = llm_base_url
        self.entity_extract_llm_type = entity_extract_llm_type
        self.entity_extract_llm_key = entity_extract_llm_key
        self.rdf_build_llm_type = rdf_build_llm_type
        self.rdf_build_llm_key = rdf_build_llm_key
        self.embed_llm_type = embed_llm_type
        self.embed_llm_key = embed_llm_key
        self.entity_file = entity_file
        self.rdf_file = rdf_file
        self.openie_file = openie_file
        self.rag_file = rag_file
        self.import_file = import_file
        self.extract_entities = extract_entities
        self.build_rdf = build_rdf
        self.build_rag = build_rag
        self.qa_llm_type = qa_llm_type
        self.qa_llm_key = qa_llm_key


parser = argparse.ArgumentParser(
    description="这是一个复现HippoRAG2的项目，使用OpenAI格式的API"
)
parser.add_argument(
    "--llm_base_url",
    type=str,
    default="http://192.168.1.9:8888/v1/",
    help="LLM服务提供商的URL",
)
parser.add_argument(
    "--entity_extract_llm_type",
    type=str,
    default="deepseek-r1-distill-llama-8b",
    help="用于实体提取的LLM模型的类型",
)
parser.add_argument(
    "--entity_extract_llm_key",
    type=str,
    default="lm-studio",
    help="用于实体提取的LLM模型的KEY",
)
parser.add_argument(
    "--rdf_build_llm_type",
    type=str,
    default="deepseek-r1-distill-llama-8b",
    help="用于RDF构建的LLM模型的类型",
)
parser.add_argument(
    "--rdf_build_llm_key",
    type=str,
    default="lm-studio",
    help="用于RDF构建的LLM模型的KEY",
)
parser.add_argument(
    "--embed_llm_type",
    type=str,
    default="text-embedding-bge-m3",
    help="用于文本嵌入的LLM模型的类型",
)
parser.add_argument(
    "--embed_llm_key",
    type=str,
    default="lm-studio",
    help="用于文本嵌入的LLM模型的KEY",
)
parser.add_argument(
    "--entity_file",
    type=str,
    default="./data/entity_output.json",
    help="存储实体提取结果的文件",
)
parser.add_argument(
    "--rdf_file", type=str, default="./data/rdf_output.json", help="存储RDF的文件"
)
parser.add_argument(
    "--openie_file",
    type=str,
    default="./data/openie.json",
    help="存储OpenIE组织形式的知识库的文件",
)
parser.add_argument(
    "--rag_file", type=str, default="./data/rag_output.csv", help="存储RAG的文件"
)
parser.add_argument(
    "--import_file",
    type=str,
    default="./data/import.json",
    help="要导入构建RDF的文件",
)
parser.add_argument(
    "--qa_llm_type",
    type=str,
    default="deepseek-r1-distill-llama-8b",
    help="用于QA的LLM模型的类型",
)
parser.add_argument(
    "--qa_llm_key", type=str, default="lm-studio", help="用于QA的LLM模型的KEY"
)

args = parser.parse_args()


global_config = Config(
    args.llm_base_url,
    args.entity_extract_llm_type,
    args.entity_extract_llm_key,
    args.rdf_build_llm_type,
    args.rdf_build_llm_key,
    args.embed_llm_type,
    args.embed_llm_key,
    args.entity_file,
    args.rdf_file,
    args.openie_file,
    args.rag_file,
    args.import_file,
    True,
    True,
    True,
    args.qa_llm_type,
    args.qa_llm_key,
)
