"""
Counterfactual backtest API

input: rule_id + params via query
output: actual vs counterfactual 月度对比 + 节省金额
pos: 后端 endpoint - 让用户回看"如果当时这样做，能省多少 $"

一旦我被更新，务必更新所属文件夹的 README.md
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ....database import get_db
from src.models import Position, PositionStatus
from ....services.counterfactual import (
    RULES,
    run_all_rules,
    run_rule,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class MonthlyPoint(BaseModel):
    month: str
    actual_pnl: float
    cf_pnl: float
    savings: float
    actual_cumulative: float
    cf_cumulative: float


class RuleSummary(BaseModel):
    rule_id: str
    name_cn: str
    name_en: str
    description_cn: str
    description_en: str
    default_params: Dict


class CounterfactualResult(BaseModel):
    rule_id: str
    name_cn: str
    name_en: str
    notes: str
    notes_en: str
    params: Dict
    skipped_count: int
    actual_total_pnl: float
    counterfactual_total_pnl: float
    savings: float  # cf_total - actual_total; positive = would have helped
    savings_pct: Optional[float]  # savings / |actual_total|
    monthly: List[MonthlyPoint]
    skipped_by_symbol: Dict[str, int]


def _load_closed_positions(db: Session) -> List[Position]:
    return db.query(Position).filter(Position.status == PositionStatus.CLOSED).all()


def _to_response(result, cfg) -> CounterfactualResult:
    actual = result.actual_total_pnl
    pct: Optional[float] = None
    if abs(actual) > 1e-6:
        pct = round(result.savings / abs(actual) * 100, 2)
    return CounterfactualResult(
        rule_id=result.rule_id,
        name_cn=cfg.name_cn,
        name_en=cfg.name_en,
        notes=result.notes,
        notes_en=result.notes_en,
        params=result.params,
        skipped_count=result.skipped_count,
        actual_total_pnl=result.actual_total_pnl,
        counterfactual_total_pnl=result.counterfactual_total_pnl,
        savings=result.savings,
        savings_pct=pct,
        monthly=[MonthlyPoint(**m) for m in result.monthly],
        skipped_by_symbol=result.skipped_by_symbol,
    )


@router.get("/rules", response_model=List[RuleSummary])
async def list_rules() -> List[RuleSummary]:
    """Enumerate available counterfactual rules + default params."""
    return [
        RuleSummary(
            rule_id=cfg.rule_id,
            name_cn=cfg.name_cn,
            name_en=cfg.name_en,
            description_cn=cfg.description_cn,
            description_en=cfg.description_en,
            default_params=cfg.default_params,
        )
        for cfg in RULES.values()
    ]


@router.get("/run/{rule_id}", response_model=CounterfactualResult)
async def run_single(
    rule_id: str,
    n_losses: Optional[int] = Query(None, description="cf1 param"),
    cooldown_hours: Optional[float] = Query(None, description="cf2 param"),
    min_trades: Optional[int] = Query(None, description="cf3 param"),
    max_win_rate: Optional[float] = Query(None, description="cf3 param"),
    cap_multiple: Optional[float] = Query(None, description="cf4 param"),
    threshold_pct: Optional[float] = Query(None, description="cf5 param"),
    db: Session = Depends(get_db),
) -> CounterfactualResult:
    if rule_id not in RULES:
        raise HTTPException(404, f"Unknown rule: {rule_id}")
    params: Dict = {}
    if n_losses is not None:
        params["n_losses"] = n_losses
    if cooldown_hours is not None:
        params["cooldown_hours"] = cooldown_hours
    if min_trades is not None:
        params["min_trades"] = min_trades
    if max_win_rate is not None:
        params["max_win_rate"] = max_win_rate
    if cap_multiple is not None:
        params["cap_multiple"] = cap_multiple
    if threshold_pct is not None:
        params["threshold_pct"] = threshold_pct

    positions = _load_closed_positions(db)
    if not positions:
        raise HTTPException(400, "No closed positions to backtest.")

    result = run_rule(positions, rule_id, params)
    return _to_response(result, RULES[rule_id])


@router.get("/summary", response_model=List[CounterfactualResult])
async def summary(db: Session = Depends(get_db)) -> List[CounterfactualResult]:
    """Run every rule with defaults, sorted by savings desc.

    Lets the UI show 'top 3 most impactful behavioral changes' at a glance.
    """
    positions = _load_closed_positions(db)
    if not positions:
        raise HTTPException(400, "No closed positions to backtest.")

    results = run_all_rules(positions)
    results_sorted = sorted(results, key=lambda r: r.savings, reverse=True)
    # Each result's rule_id carries a param suffix (e.g. "cf1_consec_loss_n3");
    # map back to the registry key to look up display names.
    return [
        _to_response(r, RULES[_strip_param_suffix(r.rule_id)])
        for r in results_sorted
    ]


def _strip_param_suffix(suffixed_id: str) -> str:
    """e.g. 'cf1_consec_loss_n3' → 'cf1_consec_loss'."""
    for rid in RULES.keys():
        if suffixed_id.startswith(rid):
            return rid
    return suffixed_id
