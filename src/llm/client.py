"""
LLM Client - OpenAI-compatible Large Language Model Client

Supports OpenAI, DeepSeek, Qwen, Moonshot, Ollama and other services
"""

from typing import Dict, List, Any

from loguru import logger
from openai import OpenAI


class LLMClient:
    """OpenAI-compatible LLM client"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM client

        Args:
            config: Configuration dictionary containing:
                - base_url: API base URL (default https://api.openai.com/v1)
                - api_key: API key
                - model: Model name (default gpt-4-turbo-preview)
                - temperature: Temperature parameter (default 0.3)
                - max_tokens: Maximum tokens (default 4096)
        """
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        self.api_key = config['api_key']
        self.model = config.get('model', 'gpt-4-turbo-preview')
        self.temperature = config.get('temperature', 0.3)
        self.max_tokens = config.get('max_tokens', 4096)

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        logger.info(f"LLM Client initialized: {self.model} @ {self.base_url}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        response_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Call LLM for chat completion

        Args:
            messages: List of messages, format [{"role": "user", "content": "..."}]
            response_format: Response format ("text" or "json")

        Returns:
            Dictionary containing response content, model, token count, and finish reason
        """
        try:
            kwargs = {
                'model': self.model,
                'messages': messages,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            }

            # GPT-4 supports JSON response format
            if response_format == "json" and "gpt-4" in self.model:
                kwargs['response_format'] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)

            result = {
                'content': response.choices[0].message.content,
                'model': response.model,
                'tokens': response.usage.total_tokens,
                'finish_reason': response.choices[0].finish_reason
            }

            logger.info(f"LLM response: {result['tokens']} tokens")
            return result

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def is_available(self) -> bool:
        """
        Check if LLM service is available

        Returns:
            True if service is available
        """
        try:
            response = self.chat([{"role": "user", "content": "ping"}])
            return response is not None
        except Exception:
            return False
