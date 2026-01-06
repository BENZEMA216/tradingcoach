"""
OpenAI LLM Client

使用 OpenAI API 调用 GPT 模型
"""

import os
import logging
from typing import Optional, List

from .base import LLMClient, LLMResponse, Message

logger = logging.getLogger(__name__)

# 延迟导入 openai，避免未安装时报错
openai = None


def _ensure_openai():
    """确保 openai 库已导入"""
    global openai
    if openai is None:
        try:
            import openai as _openai
            openai = _openai
        except ImportError:
            raise ImportError(
                "openai package is not installed. "
                "Install it with: pip install openai"
            )


class OpenAIClient(LLMClient):
    """
    OpenAI GPT 客户端

    支持 GPT-4, GPT-4o, GPT-3.5 等模型
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化 OpenAI 客户端

        Args:
            api_key: API 密钥（如果不提供，从环境变量 OPENAI_API_KEY 读取）
            model: 模型名称（默认使用 gpt-4o-mini）
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        model = model or self.DEFAULT_MODEL

        super().__init__(api_key=api_key, model=model)

        self._client = None

    def _get_client(self):
        """获取或创建 OpenAI 客户端"""
        if self._client is None:
            _ensure_openai()
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    def get_provider_name(self) -> str:
        return "openai"

    def get_default_model(self) -> str:
        return self.DEFAULT_MODEL

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本

        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
            max_tokens: 最大生成 token 数
            temperature: 生成温度

        Returns:
            LLMResponse 对象
        """
        messages = [Message(role="user", content=prompt)]
        return await self.chat(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    async def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        多轮对话

        Args:
            messages: 消息列表
            system_prompt: 系统提示（可选）
            max_tokens: 最大生成 token 数
            temperature: 生成温度

        Returns:
            LLMResponse 对象
        """
        if not self.is_available():
            raise ValueError("OpenAI API key is not set")

        client = self._get_client()

        # 构建消息列表
        api_messages = []

        # 添加系统提示
        if system_prompt:
            api_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 添加对话消息
        for msg in messages:
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        try:
            # 调用 API
            response = client.chat.completions.create(
                model=self.get_model(),
                messages=api_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # 提取响应内容
            choice = response.choices[0] if response.choices else None
            content = choice.message.content if choice else ""

            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
                finish_reason=choice.finish_reason if choice else None,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        if not super().is_available():
            return False

        # 检查 openai 库是否可用
        try:
            _ensure_openai()
            return True
        except ImportError:
            return False
