"""
First-party analytics (privacy-light, no third party)

input: anonymous funnel events from the frontend
output: appended JSONL on the persistent volume + an admin funnel summary
pos: lets the distribution-lab measure visits → sample → upload without
     loading a China-blocked third-party script. No PII: anon id + event name.

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter()

# 允许的事件名白名单（防止脏数据 / 滥用塞垃圾）
ALLOWED_EVENTS = {
    "page_view",
    "sample_click",
    "sample_loaded",
    "upload_submit",
    "analysis_complete",
}


def _analytics_file() -> Path:
    explicit = os.getenv("ANALYTICS_DIR")
    if explicit:
        base = Path(explicit)
    else:
        ws = os.getenv("WORKSPACE_DATA_DIR", "data/workspaces")
        base = Path(ws).parent
    base.mkdir(parents=True, exist_ok=True)
    return base / "analytics.jsonl"


class EventIn(BaseModel):
    name: str = Field(..., max_length=40)
    anon_id: Optional[str] = Field(None, max_length=64)
    path: Optional[str] = Field(None, max_length=200)
    ref: Optional[str] = Field(None, max_length=120)  # 渠道标记，如 xhs


@router.post("/event", status_code=status.HTTP_204_NO_CONTENT)
async def track_event(event: EventIn, request: Request) -> None:
    """记录一个匿名事件（fire-and-forget）。未知事件名静默忽略。"""
    if event.name not in ALLOWED_EVENTS:
        return None
    record = {
        "t": datetime.now(timezone.utc).isoformat(),
        "ts": time.time(),
        "name": event.name,
        "anon": (event.anon_id or "")[:64],
        "path": (event.path or "")[:200],
        "ref": (event.ref or "")[:120],
    }
    try:
        with _analytics_file().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # 埋点绝不能影响用户请求
        pass
    return None


@router.get("/summary")
async def summary(
    days: int = 7,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
):
    """漏斗汇总（受 ADMIN_TOKEN 保护）。返回访客/各事件计数 + 转化率。"""
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and x_admin_token != admin_token:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Admin-Token.")

    path = _analytics_file()
    cutoff = time.time() - days * 86400
    by_name: Counter = Counter()
    visitors: set = set()
    uploaders: set = set()
    samplers: set = set()
    by_ref: Counter = Counter()
    by_day: defaultdict = defaultdict(Counter)

    if path.exists():
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("ts", 0) < cutoff:
                    continue
                name = r.get("name", "")
                anon = r.get("anon") or ""
                by_name[name] += 1
                day = (r.get("t") or "")[:10]
                if day:
                    by_day[day][name] += 1
                if anon:
                    visitors.add(anon)
                    if name == "upload_submit":
                        uploaders.add(anon)
                    if name in ("sample_click", "sample_loaded"):
                        samplers.add(anon)
                if r.get("ref"):
                    by_ref[r["ref"]] += 1

    v = len(visitors)
    return {
        "window_days": days,
        "unique_visitors": v,
        "events": dict(by_name),
        "funnel": {
            "visitors": v,
            "tried_sample": len(samplers),
            "uploaded_csv": len(uploaders),
            "sample_rate": round(len(samplers) / v, 3) if v else 0,
            "upload_rate": round(len(uploaders) / v, 3) if v else 0,
        },
        "by_channel": dict(by_ref),
        "by_day": {d: dict(c) for d, c in sorted(by_day.items())},
    }
