from openai import OpenAI

class OpenAIClient(OpenAI):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        super().__init__(api_key=self.api_key, base_url=self.base_url)