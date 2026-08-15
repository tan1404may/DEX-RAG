import os
from typing import Optional


class LLMClient:
    """Generic LLM client. Supports OpenAI and Google Gemini."""
    
    def __init__(
        self,
        provider: str = "gemini",
        model: str = None,
        api_key: str = None,
    ):
        self.provider = provider.lower()
        self.model = model or self._default_model()
        self.api_key = api_key or self._get_api_key()
        self._client = None
    
    def _default_model(self) -> str:
        if self.provider == "gemini":
            return "gemini-1.5-flash"
        return "gpt-4o-mini"
    
    def _get_api_key(self) -> str:
        if self.provider == "gemini":
            return os.getenv("GEMINI_API_KEY", "")
        return os.getenv("OPENAI_API_KEY", "")
    
    @property
    def client(self):
        if self._client is None:
            if self.provider == "gemini":
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
 
        return self._client
    
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.3) -> str:
        if self.provider == "gemini":
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
            )
            return response.text
        
        # OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content