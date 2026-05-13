"""
Feedback API - 用户反馈自动提交到 GitHub Issues

input: 用户反馈表单数据
output: 创建 GitHub Issue
pos: 收集用户反馈，自动创建 Issue（带每 IP 限流防刷）
"""

import asyncio
import os
import time
import httpx
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# GitHub 配置
GITHUB_REPO = "BENZEMA216/tradingcoach"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/issues"

# 每 IP 限流：滑动窗口
# 配置：60 秒内最多 RATE_LIMIT_MAX 次提交。可通过 env 调整。
RATE_LIMIT_WINDOW_S = int(os.getenv("FEEDBACK_RATE_LIMIT_WINDOW_S", "60"))
RATE_LIMIT_MAX = int(os.getenv("FEEDBACK_RATE_LIMIT_MAX", "5"))
_rate_state: dict[str, list[float]] = {}
_rate_lock = asyncio.Lock()


async def _check_rate_limit(client_ip: str) -> None:
    """超过窗口阈值则抛 429。同进程内存计数，部署多副本时建议接 Redis。"""
    now = time.monotonic()
    window_start = now - RATE_LIMIT_WINDOW_S
    async with _rate_lock:
        timestamps = _rate_state.get(client_ip, [])
        timestamps = [t for t in timestamps if t > window_start]
        if len(timestamps) >= RATE_LIMIT_MAX:
            retry_after = int(timestamps[0] + RATE_LIMIT_WINDOW_S - now) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many feedback submissions. Retry in {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )
        timestamps.append(now)
        _rate_state[client_ip] = timestamps


def _sanitize_for_markdown(text: str) -> str:
    """剥掉 markdown 注入面：fenced code 反引号、HTML 标签、@提及。

    不试图防住所有 markdown 渲染怪招 — GitHub Issue 的渲染面是受限的，
    主要目标是阻止：
      * <script> / iframe 等 HTML 注入（GitHub 实际会清，但兜底）
      * 大量 ```...``` 围栏破坏 issue 排版
      * @bot / @everyone 风格的提及通知
    """
    if not text:
        return text
    # 中和反引号（避免 markdown fenced code）— 替成全宽反引号，视觉接近但不参与渲染
    out = text.replace("`", "ˋ")
    # 中和 HTML 标签开闭
    out = out.replace("<", "&lt;").replace(">", "&gt;")
    # 中和 @ 提及（在前面加零宽空格使其不再触发 GitHub 通知）
    out = out.replace("@", "@​")
    return out


class FeedbackRequest(BaseModel):
    """反馈请求"""
    type: str = Field(..., description="反馈类型: bug, feature, question")
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    description: Optional[str] = Field(None, max_length=5000, description="详细描述")
    user_agent: Optional[str] = Field(None, max_length=500, description="浏览器信息")
    page_url: Optional[str] = Field(None, max_length=500, description="当前页面URL")


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
async def submit_feedback(
    feedback: FeedbackRequest,
    request: Request,
) -> FeedbackResponse:
    """
    提交用户反馈，自动创建 GitHub Issue。

    保护层：
    1) 每 IP 60s/5 次限流（防止匿名脚本刷 GitHub Issue tracker）
    2) 标题/描述/UA/URL 做 markdown 注入净化
    3) 未配置 GITHUB_TOKEN 时返回 503
    """
    client_ip = (request.client.host if request.client else "unknown") or "unknown"
    # 反代后取真实 IP（X-Forwarded-For 第一个）
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        client_ip = fwd.split(",")[0].strip() or client_ip
    await _check_rate_limit(client_ip)

    # 获取 GitHub Token
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        logger.warning("GITHUB_TOKEN not configured, feedback submission disabled")
        raise HTTPException(
            status_code=503,
            detail="Feedback submission is not configured. Please contact support."
        )

    # 反馈类型白名单
    if feedback.type not in {"bug", "feature", "question"}:
        raise HTTPException(status_code=400, detail="Unsupported feedback type.")

    # 构建 Issue 内容（全部 sanitize）
    safe_title = _sanitize_for_markdown(feedback.title)
    safe_desc = _sanitize_for_markdown(feedback.description or "(无详细描述)")
    safe_url = _sanitize_for_markdown(feedback.page_url or "")
    safe_ua = _sanitize_for_markdown(feedback.user_agent or "")
    type_emoji = {"bug": "🐛", "feature": "💡", "question": "❓"}.get(feedback.type, "📝")

    body_parts = [
        f"## {type_emoji} 反馈内容",
        "",
        safe_desc,
        "",
        "---",
        "*通过应用内反馈提交*",
    ]

    if safe_url or safe_ua:
        body_parts.extend([
            "",
            "<details>",
            "<summary>技术信息</summary>",
            "",
        ])
        if safe_url:
            body_parts.append(f"- **页面**: {safe_url}")
        if safe_ua:
            body_parts.append(f"- **浏览器**: {safe_ua}")
        body_parts.extend(["", "</details>"])

    issue_data = {
        "title": f"[{feedback.type.upper()}] {safe_title}",
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
                    status_code=502,
                    detail="Failed to submit feedback. Please try again later."
                )

    except httpx.TimeoutException:
        logger.error("GitHub API timeout")
        raise HTTPException(
            status_code=504,
            detail="Request timeout. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again later."
        )
