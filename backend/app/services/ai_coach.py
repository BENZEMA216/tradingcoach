"""
AI Coach Service - AI 交易教练服务

整合洞察引擎和 LLM，提供智能交易分析和对话功能
"""

import os
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from .insight_engine import InsightEngine
from .llm import LLMClient, AnthropicClient, OpenAIClient
from .llm.base import Message, LLMResponse
from .prompts.templates import (
    PROACTIVE_SUMMARY_PROMPT,
    CHAT_SYSTEM_PROMPT,
    INSIGHT_ANALYSIS_PROMPT,
    QUICK_QUESTIONS,
)
from ..database import Position, PositionStatus
from ..schemas.insights import TradingInsight

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """对话消息"""
    role: str       # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ProactiveInsightResponse:
    """主动推送洞察响应"""
    insights: List[TradingInsight]      # 规则引擎生成的洞察
    ai_summary: str                      # AI 生成的总结
    key_metrics: Dict[str, Any]          # 关键指标
    date_range: Dict[str, str]           # 时间范围
    generated_at: str                    # 生成时间

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insights": [i.dict() for i in self.insights],
            "ai_summary": self.ai_summary,
            "key_metrics": self.key_metrics,
            "date_range": self.date_range,
            "generated_at": self.generated_at,
        }


@dataclass
class ChatResponse:
    """对话响应"""
    answer: str                          # AI 回答
    supporting_data: Optional[Dict[str, Any]] = None  # 支持数据
    related_insights: Optional[List[TradingInsight]] = None  # 相关洞察

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "answer": self.answer,
        }
        if self.supporting_data:
            result["supporting_data"] = self.supporting_data
        if self.related_insights:
            result["related_insights"] = [i.dict() for i in self.related_insights]
        return result


def get_llm_client() -> LLMClient:
    """
    获取 LLM 客户端

    根据配置和可用性选择合适的 LLM 后端
    """
    # 优先使用 Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        client = AnthropicClient(api_key=anthropic_key)
        if client.is_available():
            logger.info("Using Anthropic Claude as LLM backend")
            return client

    # 备选 OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        client = OpenAIClient(api_key=openai_key)
        if client.is_available():
            logger.info("Using OpenAI GPT as LLM backend")
            return client

    raise ValueError(
        "No LLM client available. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY "
        "environment variable."
    )


class AICoach:
    """
    AI 交易教练

    提供两种模式：
    1. 主动推送：定期分析并生成洞察总结
    2. 问答对话：回答用户关于交易的问题
    """

    def __init__(self, db: Session, llm_client: Optional[LLMClient] = None):
        """
        初始化 AI Coach

        Args:
            db: 数据库会话
            llm_client: LLM 客户端（可选，不提供则自动选择）
        """
        self.db = db
        self.insight_engine = InsightEngine(db)
        self._llm_client = llm_client

    @property
    def llm_client(self) -> LLMClient:
        """延迟加载 LLM 客户端"""
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    def _get_key_metrics(self, positions: List[Position]) -> Dict[str, Any]:
        """计算关键指标"""
        if not positions:
            return {}

        total_trades = len(positions)
        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        losers = [p for p in positions if p.net_pnl and float(p.net_pnl) <= 0]

        win_rate = len(winners) / total_trades * 100 if total_trades > 0 else 0
        total_pnl = sum(float(p.net_pnl or 0) for p in positions)
        avg_win = sum(float(p.net_pnl) for p in winners) / len(winners) if winners else 0
        avg_loss = abs(sum(float(p.net_pnl) for p in losers) / len(losers)) if losers else 0

        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "winners": len(winners),
            "losers": len(losers),
        }

    async def get_proactive_insights(
        self,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        limit: int = 10
    ) -> ProactiveInsightResponse:
        """
        获取主动推送的洞察

        Args:
            date_start: 开始日期
            date_end: 结束日期
            limit: 返回洞察数量上限

        Returns:
            ProactiveInsightResponse 包含洞察和AI总结
        """
        # 1. 运行规则引擎获取洞察
        insights = self.insight_engine.generate_insights(
            date_start=date_start,
            date_end=date_end,
            limit=limit
        )

        # 2. 获取相关持仓用于计算指标
        query = self.db.query(Position).filter(Position.status == PositionStatus.CLOSED)
        if date_start:
            query = query.filter(Position.close_date >= date_start)
        if date_end:
            query = query.filter(Position.close_date <= date_end)
        positions = query.all()

        # 3. 计算关键指标
        metrics = self._get_key_metrics(positions)

        # 4. 确定日期范围
        if positions:
            actual_start = min(p.close_date for p in positions if p.close_date)
            actual_end = max(p.close_date for p in positions if p.close_date)
            date_range_str = f"{actual_start} 至 {actual_end}"
        else:
            date_range_str = "无数据"

        # 5. 生成 AI 总结
        ai_summary = await self._generate_summary(insights, metrics, date_range_str)

        return ProactiveInsightResponse(
            insights=insights,
            ai_summary=ai_summary,
            key_metrics=metrics,
            date_range={
                "start": str(date_start) if date_start else "all",
                "end": str(date_end) if date_end else "all",
                "display": date_range_str,
            },
            generated_at=datetime.now().isoformat(),
        )

    async def _generate_summary(
        self,
        insights: List[TradingInsight],
        metrics: Dict[str, Any],
        date_range: str
    ) -> str:
        """使用 LLM 生成洞察总结"""
        if not insights:
            return "暂无足够数据生成分析报告。请确保有足够的交易记录。"

        # 将洞察转换为 JSON 格式
        insights_json = json.dumps(
            [
                {
                    "id": i.id,
                    "type": i.type.value,
                    "title": i.title,
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "priority": i.priority,
                }
                for i in insights
            ],
            ensure_ascii=False,
            indent=2
        )

        # 构建 prompt
        prompt = PROACTIVE_SUMMARY_PROMPT.format(
            date_range=date_range,
            total_trades=metrics.get("total_trades", 0),
            win_rate=metrics.get("win_rate", 0),
            total_pnl=metrics.get("total_pnl", 0),
            avg_win=metrics.get("avg_win", 0),
            avg_loss=metrics.get("avg_loss", 0),
            insights_json=insights_json,
        )

        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.7
            )
            return response.content
        except Exception as e:
            logger.error(f"Failed to generate AI summary: {e}")
            # 降级：返回简单总结
            return self._generate_fallback_summary(insights, metrics)

    def _generate_fallback_summary(
        self,
        insights: List[TradingInsight],
        metrics: Dict[str, Any]
    ) -> str:
        """生成降级版本的总结（不使用 LLM）"""
        problems = [i for i in insights if i.type.value == "problem"]
        strengths = [i for i in insights if i.type.value == "strength"]

        summary_parts = []

        # 整体表现
        win_rate = metrics.get("win_rate", 0)
        total_pnl = metrics.get("total_pnl", 0)
        pnl_status = "盈利" if total_pnl > 0 else "亏损"
        summary_parts.append(
            f"共{metrics.get('total_trades', 0)}笔交易，"
            f"胜率{win_rate:.1f}%，{pnl_status}${abs(total_pnl):,.0f}。"
        )

        # 问题
        if problems:
            summary_parts.append(f"\n\n主要问题：")
            for p in problems[:2]:
                summary_parts.append(f"- {p.title}: {p.description}")

        # 优势
        if strengths:
            summary_parts.append(f"\n\n优势方面：")
            for s in strengths[:2]:
                summary_parts.append(f"- {s.title}: {s.description}")

        return "\n".join(summary_parts)

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[ChatMessage]] = None
    ) -> ChatResponse:
        """
        对话问答

        Args:
            message: 用户消息
            conversation_history: 对话历史

        Returns:
            ChatResponse 包含回答和相关数据
        """
        conversation_history = conversation_history or []

        # 1. 获取用户数据摘要
        user_data_summary = self._get_user_data_summary()

        # 2. 获取可用洞察
        insights = self.insight_engine.generate_insights(limit=5)
        insights_summary = self._format_insights_for_prompt(insights)

        # 3. 构建系统 prompt
        system_prompt = CHAT_SYSTEM_PROMPT.format(
            user_data_summary=user_data_summary,
            available_insights=insights_summary,
        )

        # 4. 构建消息列表
        messages = []
        for hist_msg in conversation_history[-5:]:  # 只保留最近5轮
            messages.append(Message(role=hist_msg.role, content=hist_msg.content))
        messages.append(Message(role="user", content=message))

        # 5. 调用 LLM
        try:
            response = await self.llm_client.chat(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=1024,
                temperature=0.7
            )

            return ChatResponse(
                answer=response.content,
                related_insights=insights[:3] if insights else None,
            )

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return ChatResponse(
                answer="抱歉，AI 服务暂时不可用。请稍后重试或检查 API 配置。",
            )

    def _get_user_data_summary(self) -> str:
        """获取用户数据摘要"""
        positions = self.db.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        if not positions:
            return "暂无交易记录"

        metrics = self._get_key_metrics(positions)

        # 获取交易的标的
        symbols = list(set(p.symbol for p in positions))
        top_symbols = sorted(
            [(s, len([p for p in positions if p.symbol == s])) for s in symbols],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return f"""
- 总交易数: {metrics['total_trades']}笔
- 胜率: {metrics['win_rate']}%
- 总盈亏: ${metrics['total_pnl']:,.2f}
- 主要交易标的: {', '.join([f'{s}({c}笔)' for s, c in top_symbols])}
"""

    def _format_insights_for_prompt(self, insights: List[TradingInsight]) -> str:
        """格式化洞察用于 prompt"""
        if not insights:
            return "暂无洞察"

        formatted = []
        for i in insights:
            formatted.append(f"- [{i.type.value.upper()}] {i.title}: {i.description}")

        return "\n".join(formatted)

    def get_quick_questions(self) -> List[str]:
        """获取预设的快捷问题"""
        return QUICK_QUESTIONS.copy()
