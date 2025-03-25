from openai import OpenAI
import httpx


class LLMMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class LLMClient:
    """LLM客户端，对应一个API服务商"""

    def __init__(self, url, api_key):
        self.client = OpenAI(
            base_url=url,
            api_key=api_key,
            http_client=httpx.Client(verify=False)
        )

    def send_chat_request(self, model, messages):
        """发送对话请求，等待返回结果"""
        response = self.client.chat.completions.create(
            model=model, messages=messages, stream=False
        )
        return response.choices[0].message.content

    def send_embedding_request(self, model, text):
        """发送嵌入请求，等待返回结果"""
        text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(input=[text], model=model).data[0].embedding
        )
