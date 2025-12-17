"""
AI Coach API Endpoints

提供 AI 交易教练的 API 接口
"""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ....database import get_db
from ....services.ai_coach import AICoach, ChatMessage
from ....schemas.insights import TradingInsight, InsightType, InsightCategory

router = APIRouter(prefix="/ai-coach", tags=["AI Coach"])


# ==================== Request/Response Models ====================

class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息")
    history: Optional[List[dict]] = Field(default=None, description="对话历史")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "我最擅长交易哪个标的？",
                "history": [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好！我是你的交易教练AI，有什么可以帮你的？"}
                ]
            }
        }


class ChatResponseModel(BaseModel):
    """对话响应"""
    answer: str = Field(..., description="AI 回答")
    supporting_data: Optional[dict] = Field(default=None, description="支持数据")
    related_insights: Optional[List[dict]] = Field(default=None, description="相关洞察")


class ProactiveInsightResponseModel(BaseModel):
    """主动洞察响应"""
    insights: List[dict] = Field(..., description="规则引擎洞察列表")
    ai_summary: str = Field(..., description="AI 生成的总结")
    key_metrics: dict = Field(..., description="关键指标")
    date_range: dict = Field(..., description="时间范围")
    generated_at: str = Field(..., description="生成时间")


class QuickQuestionsResponse(BaseModel):
    """快捷问题响应"""
    questions: List[str] = Field(..., description="预设问题列表")


class ServiceStatusResponse(BaseModel):
    """服务状态响应"""
    available: bool = Field(..., description="服务是否可用")
    provider: Optional[str] = Field(default=None, description="LLM 提供商")
    model: Optional[str] = Field(default=None, description="使用的模型")
    message: str = Field(..., description="状态消息")


# ==================== API Endpoints ====================

@router.get(
    "/proactive-insights",
    response_model=ProactiveInsightResponseModel,
    summary="获取主动推送的洞察",
    description="运行规则引擎并使用 AI 生成洞察总结"
)
async def get_proactive_insights(
    date_start: Optional[date] = Query(default=None, description="开始日期"),
    date_end: Optional[date] = Query(default=None, description="结束日期"),
    limit: int = Query(default=10, ge=1, le=20, description="返回洞察数量上限"),
    db: Session = Depends(get_db)
):
    """
    获取主动推送的洞察

    返回规则引擎生成的洞察列表和 AI 生成的总结报告。
    """
    try:
        coach = AICoach(db)
        response = await coach.get_proactive_insights(
            date_start=date_start,
            date_end=date_end,
            limit=limit
        )
        return response.to_dict()
    except ValueError as e:
        # LLM 客户端不可用时的处理
        coach = AICoach(db)
        insights = coach.insight_engine.generate_insights(
            date_start=date_start,
            date_end=date_end,
            limit=limit
        )
        return {
            "insights": [i.dict() for i in insights],
            "ai_summary": f"AI 服务暂不可用: {str(e)}。以下是规则引擎生成的洞察。",
            "key_metrics": {},
            "date_range": {
                "start": str(date_start) if date_start else "all",
                "end": str(date_end) if date_end else "all",
            },
            "generated_at": "",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成洞察失败: {str(e)}")


@router.post(
    "/chat",
    response_model=ChatResponseModel,
    summary="与 AI 教练对话",
    description="发送消息与 AI 交易教练进行对话"
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    与 AI 教练对话

    支持多轮对话，可以询问关于交易的各种问题。
    """
    try:
        coach = AICoach(db)

        # 转换对话历史
        history = None
        if request.history:
            history = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in request.history
            ]

        response = await coach.chat(
            message=request.message,
            conversation_history=history
        )
        return response.to_dict()

    except ValueError as e:
        return {
            "answer": f"AI 服务暂不可用: {str(e)}。请检查 API 配置。",
            "supporting_data": None,
            "related_insights": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


@router.get(
    "/quick-questions",
    response_model=QuickQuestionsResponse,
    summary="获取快捷问题",
    description="获取预设的快捷问题列表"
)
async def get_quick_questions(db: Session = Depends(get_db)):
    """
    获取快捷问题列表

    返回一组预设的常见问题，用户可以快速选择。
    """
    coach = AICoach(db)
    return {"questions": coach.get_quick_questions()}


@router.get(
    "/status",
    response_model=ServiceStatusResponse,
    summary="检查服务状态",
    description="检查 AI Coach 服务是否可用"
)
async def check_status():
    """
    检查服务状态

    返回 AI Coach 服务的可用性和配置信息。
    """
    import os

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if anthropic_key:
        return {
            "available": True,
            "provider": "anthropic",
            "model": "claude-3-haiku-20240307",
            "message": "Anthropic Claude 服务可用"
        }
    elif openai_key:
        return {
            "available": True,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "message": "OpenAI GPT 服务可用"
        }
    else:
        return {
            "available": False,
            "provider": None,
            "model": None,
            "message": "未配置 LLM API Key。请设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 环境变量。"
        }


@router.get(
    "/insights-only",
    summary="仅获取规则引擎洞察",
    description="只返回规则引擎生成的洞察，不调用 LLM"
)
async def get_insights_only(
    date_start: Optional[date] = Query(default=None, description="开始日期"),
    date_end: Optional[date] = Query(default=None, description="结束日期"),
    limit: int = Query(default=10, ge=1, le=50, description="返回洞察数量上限"),
    db: Session = Depends(get_db)
):
    """
    仅获取规则引擎洞察

    不调用 LLM，直接返回规则引擎生成的洞察。
    适用于不需要 AI 总结或 LLM 不可用的场景。
    """
    try:
        coach = AICoach(db)
        insights = coach.insight_engine.generate_insights(
            date_start=date_start,
            date_end=date_end,
            limit=limit
        )
        return {
            "insights": [i.dict() for i in insights],
            "total": len(insights),
            "date_range": {
                "start": str(date_start) if date_start else "all",
                "end": str(date_end) if date_end else "all",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取洞察失败: {str(e)}")
