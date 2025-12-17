"""
Anthropic (Claude) LLM Client

使用 Anthropic API 调用 Claude 模型
"""

import os
import logging
from typing import Optional, List

from .base import LLMClient, LLMResponse, Message

logger = logging.getLogger(__name__)

# 延迟导入 anthropic，避免未安装时报错
anthropic = None


def _ensure_anthropic():
    """确保 anthropic 库已导入"""
    global anthropic
    if anthropic is None:
        try:
            import anthropic as _anthropic
            anthropic = _anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is not installed. "
                "Install it with: pip install anthropic"
            )


class AnthropicClient(LLMClient):
    """
    Anthropic Claude 客户端

    支持 Claude 3 系列模型
    """

    DEFAULT_MODEL = "claude-3-haiku-20240307"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化 Anthropic 客户端

        Args:
            api_key: API 密钥（如果不提供，从环境变量 ANTHROPIC_API_KEY 读取）
            model: 模型名称（默认使用 claude-3-haiku）
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        model = model or self.DEFAULT_MODEL

        super().__init__(api_key=api_key, model=model)

        self._client = None

    def _get_client(self):
        """获取或创建 Anthropic 客户端"""
        if self._client is None:
            _ensure_anthropic()
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def get_provider_name(self) -> str:
        return "anthropic"

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
            raise ValueError("Anthropic API key is not set")

        client = self._get_client()

        # 转换消息格式
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        try:
            # 构建请求参数
            request_params = {
                "model": self.get_model(),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": api_messages,
            }

            # 添加系统提示
            if system_prompt:
                request_params["system"] = system_prompt

            # 调用 API
            response = client.messages.create(**request_params)

            # 提取响应内容
            content = response.content[0].text if response.content else ""

            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                finish_reason=response.stop_reason,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        if not super().is_available():
            return False

        # 检查 anthropic 库是否可用
        try:
            _ensure_anthropic()
            return True
        except ImportError:
            return False
