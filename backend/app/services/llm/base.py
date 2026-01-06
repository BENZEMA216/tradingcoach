"""
LLM Client Base - 抽象基类

定义 LLM 客户端的通用接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM 响应结构"""
    content: str                          # 生成的文本内容
    model: str                            # 使用的模型
    usage: Optional[Dict[str, int]] = None  # token 使用情况
    finish_reason: Optional[str] = None   # 完成原因
    raw_response: Optional[Any] = None    # 原始响应对象


@dataclass
class Message:
    """对话消息"""
    role: str      # "user", "assistant", "system"
    content: str   # 消息内容


class LLMClient(ABC):
    """
    LLM 客户端抽象基类

    所有具体的 LLM 客户端都应该继承此类
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 密钥（如果不提供，从环境变量读取）
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """获取默认模型"""
        pass

    @abstractmethod
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
            **kwargs: 其他参数

        Returns:
            LLMResponse 对象
        """
        pass

    @abstractmethod
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
            **kwargs: 其他参数

        Returns:
            LLMResponse 对象
        """
        pass

    def is_available(self) -> bool:
        """检查客户端是否可用（API key 是否设置）"""
        return self.api_key is not None and len(self.api_key) > 0

    def get_model(self) -> str:
        """获取当前使用的模型"""
        return self.model or self.get_default_model()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.get_model()}, available={self.is_available()})"
