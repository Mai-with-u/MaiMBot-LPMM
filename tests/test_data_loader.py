import unittest
from pathlib import Path
import jsonlines
from src.utils.data_loader import DataLoader
import logging
import json


class TestDataLoader(unittest.TestCase):
    def setUp(self):
        """准备工作"""
        # 配置日志
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        self.logger = logging.getLogger(__name__)

        # 创建测试数据目录
        tests_dir = Path(__file__).parent
        self.test_data_dir = tests_dir / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

        # 创建测试用的JSONL文件
        self.test_jsonl_file = "test_data.jsonl"
        self.test_data = [
            {"id": 1, "name": "测试1"},
            {"id": 2, "name": "测试2"},
            {"id": 3, "name": "测试3"},
            {
                "id": "2hop__482757_12019",
                "paragraphs": [
                    {
                        "idx": 0,
                        "title": "Pakistan Super League",
                        "paragraph_text": "Pakistan Super League (Urdu: پاکستان سپر لیگ ‎ ‎; PSL) is a Twenty20 "
                        "cricket league, founded in Lahore on 9 September 2015 with five teams and "
                        "now comprises six teams. Instead of operating as an association of "
                        "independently owned teams, the league is a single entity in which each "
                        "franchise is owned and controlled by investors.",
                        "is_supporting": False,
                    },
                    {
                        "idx": 1,
                        "title": "Serena Wilson",
                        "paragraph_text": "Serena Wilson (August 8, 1933 – June 17, 2007), often known just as "
                        '"Serena", was a well-known dancer, choreographer, and teacher who helped '
                        "popularize belly dance in the United States. Serena's work also helped "
                        "legitimize the dance form and helped it to be perceived as more than "
                        "burlesque or stripping. Serena danced in clubs in her younger years, "
                        "opened her own studio, hosted her own television show, founded her own "
                        "dance troupe, and was the author of several books about belly dance.",
                        "is_supporting": False,
                    },
                ],
                "question": "When was the institute that owned The Collegian founded?",
                "question_decomposition": [
                    {
                        "id": 482757,
                        "question": "The Collegian >> owned by",
                        "answer": "Houston Baptist University",
                        "paragraph_support_idx": 5,
                    },
                    {
                        "id": 12019,
                        "question": "When was #1 founded?",
                        "answer": "1960",
                        "paragraph_support_idx": 9,
                    },
                ],
                "answer": "1960",
                "answer_aliases": [],
                "answerable": True,
            },
        ]

        # 写入测试数据
        with jsonlines.open(
            self.test_data_dir / self.test_jsonl_file, mode="w"
        ) as writer:
            for item in self.test_data:
                # 使用json.dumps和json.loads确保数据被正确序列化
                json_str = json.dumps(item, ensure_ascii=False)
                json_obj = json.loads(json_str)
                writer.write(json_obj)

        # 创建DataLoader实例
        self.data_loader = DataLoader(custom_data_dir=self.test_data_dir)

    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试文件
        if (self.test_data_dir / self.test_jsonl_file).exists():
            (self.test_data_dir / self.test_jsonl_file).unlink()
        # 删除测试目录
        if self.test_data_dir.exists():
            self.test_data_dir.rmdir()

    def test_load_jsonl(self):
        """测试load_jsonl方法"""
        self.logger.info("测试load_jsonl方法...")

        # 测试正常加载
        loaded_data = self.data_loader.load_jsonl(self.test_jsonl_file)
        self.assertEqual(loaded_data, self.test_data)

        # 测试文件不存在的情况
        with self.assertRaises(FileNotFoundError):
            self.data_loader.load_jsonl("不存在的文件.jsonl")

        self.logger.info("✓ load_jsonl测试通过")


if __name__ == "__main__":
    unittest.main()
