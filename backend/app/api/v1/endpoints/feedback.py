"""
Feedback API - 用户反馈自动提交到 GitHub Issues

input: 用户反馈表单数据
output: 创建 GitHub Issue
pos: 收集用户反馈，自动创建 Issue
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# GitHub 配置
GITHUB_REPO = "BENZEMA216/tradingcoach"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/issues"


class FeedbackRequest(BaseModel):
    """反馈请求"""
    type: str = Field(..., description="反馈类型: bug, feature, question")
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    description: Optional[str] = Field(None, max_length=5000, description="详细描述")
    user_agent: Optional[str] = Field(None, description="浏览器信息")
    page_url: Optional[str] = Field(None, description="当前页面URL")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    success: bool
    message: str
    issue_url: Optional[str] = None
    issue_number: Optional[int] = None


def get_label_for_type(feedback_type: str) -> str:
    """根据反馈类型返回 GitHub label"""
    labels = {
        "bug": "bug",
        "feature": "enhancement",
        "question": "question",
    }
    return labels.get(feedback_type, "feedback")


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest) -> FeedbackResponse:
    """
    提交用户反馈，自动创建 GitHub Issue
    """
    # 获取 GitHub Token
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        logger.warning("GITHUB_TOKEN not configured, feedback submission disabled")
        raise HTTPException(
            status_code=503,
            detail="Feedback submission is not configured. Please contact support."
        )

    # 构建 Issue 内容
    type_emoji = {"bug": "🐛", "feature": "💡", "question": "❓"}.get(feedback.type, "📝")

    body_parts = [
        f"## {type_emoji} 反馈内容",
        "",
        feedback.description or "(无详细描述)",
        "",
        "---",
        "*通过应用内反馈提交*",
    ]

    # 添加技术信息
    if feedback.page_url or feedback.user_agent:
        body_parts.extend([
            "",
            "<details>",
            "<summary>技术信息</summary>",
            "",
        ])
        if feedback.page_url:
            body_parts.append(f"- **页面**: {feedback.page_url}")
        if feedback.user_agent:
            body_parts.append(f"- **浏览器**: {feedback.user_agent}")
        body_parts.extend(["", "</details>"])

    issue_data = {
        "title": f"[{feedback.type.upper()}] {feedback.title}",
        "body": "\n".join(body_parts),
        "labels": [get_label_for_type(feedback.type), "user-feedback"],
    }

    # 调用 GitHub API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_API_URL,
                json=issue_data,
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=10.0,
            )

            if response.status_code == 201:
                result = response.json()
                logger.info(f"Feedback submitted successfully: Issue #{result['number']}")
                return FeedbackResponse(
                    success=True,
                    message="感谢你的反馈！我们已收到。",
                    issue_url=result["html_url"],
                    issue_number=result["number"],
                )
            else:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to submit feedback. Please try again later."
                )

    except httpx.TimeoutException:
        logger.error("GitHub API timeout")
        raise HTTPException(
            status_code=504,
            detail="Request timeout. Please try again."
        )
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again later."
        )
