"""
Counterfactual backtest engine

input: 已经平仓的 Position 列表 + 一条反事实规则
output: 该规则下"如果当时这样做能省/赚多少 $"的对比结果
pos: 业务层 - 让 AI Coach 不只是说"你连亏 10 笔"，而是真算出避开后的累计影响

设计原则：
- 规则只能依赖"当时已知的信息"——交易序号在前的位置可以影响交易序号在后的，
  反过来不行（否则就是 look-ahead bias）。
- 所有金额一律换算到 USD（用 backend.app.utils.currency.get_pnl_in_usd），
  否则 HKD 跟 USD 加减毫无意义。
- 每条规则都返回完整的月度曲线对比，让前端可以画"actual vs counterfactual"。

一旦我被更新，务必更新所属文件夹的 README.md
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from src.models import Position, PositionStatus
from ..utils.currency import get_pnl_in_usd


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

@dataclass
class RuleConfig:
    rule_id: str
    name_cn: str
    name_en: str
    description_cn: str
    description_en: str
    default_params: Dict
    apply: Callable[[List[Position], Dict], "RuleResult"]


@dataclass
class RuleResult:
    """Per-rule output."""
    rule_id: str
    params: Dict
    skipped_position_ids: List[int]
    skipped_count: int
    actual_total_pnl: float
    counterfactual_total_pnl: float
    savings: float  # cf - actual; positive = counterfactual would have done better
    monthly: List[Dict]  # [{month: "2025-04", actual_pnl, cf_pnl, savings}, ...]
    skipped_by_symbol: Dict[str, int]
    notes: str = ""
    notes_en: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _close_date(p: Position) -> date:
    return p.close_date or p.open_date


def _month_key(d: Optional[date]) -> str:
    if d is None:
        return "?"
    return f"{d.year:04d}-{d.month:02d}"


def _sort_chronological(positions: List[Position]) -> List[Position]:
    return sorted(positions, key=lambda p: (_close_date(p), p.id))


def _pnl_usd(p: Position) -> float:
    return get_pnl_in_usd(p)


def _build_monthly(
    positions: List[Position],
    skip_set: set,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Return (actual_by_month, counterfactual_by_month) keyed by YYYY-MM."""
    actual: Dict[str, float] = defaultdict(float)
    counter: Dict[str, float] = defaultdict(float)
    for p in positions:
        m = _month_key(_close_date(p))
        v = _pnl_usd(p)
        actual[m] += v
        if p.id not in skip_set:
            counter[m] += v
    return actual, counter


def _assemble_result(
    rule_id: str,
    params: Dict,
    positions: List[Position],
    skipped_ids: List[int],
    notes: str = "",
    notes_en: str = "",
) -> RuleResult:
    skip_set = set(skipped_ids)
    actual_by_m, counter_by_m = _build_monthly(positions, skip_set)
    all_months = sorted(set(actual_by_m.keys()) | set(counter_by_m.keys()))

    actual_total = sum(actual_by_m.values())
    counter_total = sum(counter_by_m.values())

    monthly_rows: List[Dict] = []
    cum_actual = 0.0
    cum_cf = 0.0
    for m in all_months:
        a = round(actual_by_m.get(m, 0.0), 2)
        c = round(counter_by_m.get(m, 0.0), 2)
        cum_actual += a
        cum_cf += c
        monthly_rows.append({
            "month": m,
            "actual_pnl": a,
            "cf_pnl": c,
            "savings": round(c - a, 2),
            "actual_cumulative": round(cum_actual, 2),
            "cf_cumulative": round(cum_cf, 2),
        })

    # skipped by symbol
    by_sym: Dict[str, int] = defaultdict(int)
    skipped_by_id = {p.id: p for p in positions if p.id in skip_set}
    for p in skipped_by_id.values():
        by_sym[p.symbol] += 1

    return RuleResult(
        rule_id=rule_id,
        params=params,
        skipped_position_ids=skipped_ids,
        skipped_count=len(skipped_ids),
        actual_total_pnl=round(actual_total, 2),
        counterfactual_total_pnl=round(counter_total, 2),
        savings=round(counter_total - actual_total, 2),
        monthly=monthly_rows,
        skipped_by_symbol=dict(by_sym),
        notes=notes,
        notes_en=notes_en,
    )


# ---------------------------------------------------------------------------
# Rule implementations
# ---------------------------------------------------------------------------

def cf1_consecutive_loss_cutoff(
    positions: List[Position], params: Dict
) -> RuleResult:
    """Per ticker, after N consecutive losses, skip all subsequent positions
    on that ticker."""
    n = int(params.get("n_losses", 3))
    chrono = _sort_chronological(positions)

    cutoff_after_id: Dict[str, int] = {}  # symbol -> position_id triggering cutoff
    loss_streak: Dict[str, int] = defaultdict(int)
    skipped: List[int] = []

    for p in chrono:
        sym = p.symbol
        # 已被熔断 → 跳过 (该交易开仓时已满足熔断条件)
        if sym in cutoff_after_id:
            skipped.append(p.id)
            continue
        pnl = _pnl_usd(p)
        if pnl < 0:
            loss_streak[sym] += 1
            if loss_streak[sym] >= n:
                # 当前这笔仍然发生；从下一笔开始熔断
                cutoff_after_id[sym] = p.id
        else:
            loss_streak[sym] = 0

    return _assemble_result(
        rule_id=f"cf1_consec_loss_n{n}",
        params={"n_losses": n},
        positions=positions,
        skipped_ids=skipped,
        notes=(
            f"对每个标的，连续 {n} 笔亏损后跳过该标的所有后续交易。"
            f"触发熔断的标的：{len(cutoff_after_id)} 个。"
        ),
        notes_en=(
            f"Per ticker, skip all later trades on it after {n} consecutive losses. "
            f"Tickers that triggered the cutoff: {len(cutoff_after_id)}."
        ),
    )


def cf2_no_revenge_trading(
    positions: List[Position], params: Dict
) -> RuleResult:
    """After any loss, skip the next position if it opens within X hours."""
    hours = float(params.get("cooldown_hours", 2.0))
    cooldown = timedelta(hours=hours)
    chrono = _sort_chronological(positions)

    skipped: List[int] = []
    last_loss_close: Optional[datetime] = None

    for p in chrono:
        opened = p.open_time or (
            datetime.combine(p.open_date, datetime.min.time())
            if p.open_date else None
        )
        if (
            last_loss_close is not None
            and opened is not None
            and opened - last_loss_close <= cooldown
        ):
            skipped.append(p.id)
            # Skipped trades don't propagate "last loss" further
            continue

        # Update last_loss_close based on outcome
        if _pnl_usd(p) < 0:
            last_loss_close = p.close_time or (
                datetime.combine(p.close_date, datetime.min.time())
                if p.close_date else None
            )
        else:
            last_loss_close = None

    return _assemble_result(
        rule_id=f"cf2_no_revenge_{int(hours)}h",
        params={"cooldown_hours": hours},
        positions=positions,
        skipped_ids=skipped,
        notes=(
            f"任何亏损平仓后 {hours} 小时内开的新仓视为报复性交易，全部跳过。"
        ),
        notes_en=(
            f"Any position opened within {hours}h of a losing exit is treated as "
            f"revenge trading and skipped."
        ),
    )


def cf3_avoid_persistent_losers(
    positions: List[Position], params: Dict
) -> RuleResult:
    """Skip all positions on tickers whose overall win rate < threshold AND
    total P&L < 0 over the period. Uses full-period stats — this is a
    'looking back, you should have known' rule, not look-ahead bias because
    the recommendation is about future behavior."""
    min_trades = int(params.get("min_trades", 5))
    max_win_rate = float(params.get("max_win_rate", 0.40))

    # Per-symbol stats over the whole period
    sym_stats: Dict[str, Dict] = defaultdict(lambda: {"wins": 0, "trades": 0, "pnl": 0.0})
    for p in positions:
        s = sym_stats[p.symbol]
        s["trades"] += 1
        s["pnl"] += _pnl_usd(p)
        if _pnl_usd(p) > 0:
            s["wins"] += 1

    bad_symbols = {
        sym for sym, st in sym_stats.items()
        if st["trades"] >= min_trades
        and st["wins"] / st["trades"] < max_win_rate
        and st["pnl"] < 0
    }

    skipped = [p.id for p in positions if p.symbol in bad_symbols]

    return _assemble_result(
        rule_id=f"cf3_avoid_losers_wr{int(max_win_rate*100)}",
        params={"min_trades": min_trades, "max_win_rate": max_win_rate},
        positions=positions,
        skipped_ids=skipped,
        notes=(
            f"完全避开胜率 < {max_win_rate*100:.0f}% 且总盈亏 < 0 的标的"
            f"（最少 {min_trades} 笔样本）。识别出 {len(bad_symbols)} 个标的："
            f"{', '.join(sorted(bad_symbols)[:8])}{'...' if len(bad_symbols)>8 else ''}"
        ),
        notes_en=(
            f"Fully avoid tickers with win rate < {max_win_rate*100:.0f}% and "
            f"negative total P&L (min {min_trades} trades). "
            f"Identified {len(bad_symbols)} tickers: "
            f"{', '.join(sorted(bad_symbols)[:8])}{'...' if len(bad_symbols)>8 else ''}"
        ),
    )


def cf4_position_size_cap(
    positions: List[Position], params: Dict
) -> RuleResult:
    """Cap any single position to N× the rolling-median position size at the
    time of opening. We approximate the median by using all positions BEFORE
    this one (no look-ahead). When a position exceeds the cap, scale its
    P&L proportionally (qty × cost-per-share is roughly linear in qty)."""
    cap_multiple = float(params.get("cap_multiple", 3.0))
    chrono = _sort_chronological(positions)

    # 不真的"跳过"，而是按比例缩小 P&L → 给特殊处理
    # 用一个虚拟的 "savings" 来表达：减小的亏损/盈利
    actual_by_m: Dict[str, float] = defaultdict(float)
    counter_by_m: Dict[str, float] = defaultdict(float)
    capped_positions: List[int] = []
    sizes_so_far: List[float] = []

    def _size(p: Position) -> float:
        try:
            op = float(p.open_price or 0)
            q = float(p.quantity or 0)
            mult = 100 if p.is_option else 1
            return op * q * mult
        except Exception:
            return 0.0

    for p in chrono:
        m = _month_key(_close_date(p))
        pnl = _pnl_usd(p)
        actual_by_m[m] += pnl

        my_size = _size(p)
        if sizes_so_far:
            sorted_sizes = sorted(sizes_so_far)
            median = sorted_sizes[len(sorted_sizes) // 2]
            cap = max(median * cap_multiple, 1.0)
            if my_size > cap and my_size > 0:
                ratio = cap / my_size
                counter_by_m[m] += pnl * ratio
                capped_positions.append(p.id)
            else:
                counter_by_m[m] += pnl
        else:
            counter_by_m[m] += pnl

        if my_size > 0:
            sizes_so_far.append(my_size)

    all_months = sorted(set(actual_by_m.keys()) | set(counter_by_m.keys()))
    actual_total = sum(actual_by_m.values())
    counter_total = sum(counter_by_m.values())

    monthly_rows: List[Dict] = []
    cum_a = 0.0
    cum_c = 0.0
    for m in all_months:
        a = round(actual_by_m.get(m, 0.0), 2)
        c = round(counter_by_m.get(m, 0.0), 2)
        cum_a += a
        cum_c += c
        monthly_rows.append({
            "month": m,
            "actual_pnl": a,
            "cf_pnl": c,
            "savings": round(c - a, 2),
            "actual_cumulative": round(cum_a, 2),
            "cf_cumulative": round(cum_c, 2),
        })

    by_sym: Dict[str, int] = defaultdict(int)
    capped_ids = set(capped_positions)
    for p in positions:
        if p.id in capped_ids:
            by_sym[p.symbol] += 1

    return RuleResult(
        rule_id=f"cf4_size_cap_{int(cap_multiple)}x",
        params={"cap_multiple": cap_multiple},
        skipped_position_ids=capped_positions,
        skipped_count=len(capped_positions),
        actual_total_pnl=round(actual_total, 2),
        counterfactual_total_pnl=round(counter_total, 2),
        savings=round(counter_total - actual_total, 2),
        monthly=monthly_rows,
        skipped_by_symbol=dict(by_sym),
        notes=(
            f"单笔仓位金额超过历史中位数的 {cap_multiple}× 时按比例缩小，"
            f"模拟仓位管理对总盈亏的影响。命中 {len(capped_positions)} 笔。"
        ),
        notes_en=(
            f"Scale down any position larger than {cap_multiple}× the historical "
            f"median size, simulating position-size management. "
            f"{len(capped_positions)} positions affected."
        ),
    )


def cf5_hard_stop_loss(
    positions: List[Position], params: Dict
) -> RuleResult:
    """If a position's final realized pnl% is worse than -X%, cap the loss
    at -X% of cost basis. This simulates a hard stop being honored."""
    threshold_pct = float(params.get("threshold_pct", -10.0))  # negative number
    capped: List[int] = []
    actual_by_m: Dict[str, float] = defaultdict(float)
    counter_by_m: Dict[str, float] = defaultdict(float)

    for p in positions:
        m = _month_key(_close_date(p))
        pnl_usd = _pnl_usd(p)
        actual_by_m[m] += pnl_usd

        # Compare in same currency the pnl_pct was computed in (it's currency-neutral
        # because it's a ratio of two values in the same currency).
        pct = p.net_pnl_pct
        if pct is not None and float(pct) < threshold_pct:
            # Reconstruct cost basis from open_price, qty, multiplier
            mult = 100 if p.is_option else 1
            cost = float(p.open_price or 0) * float(p.quantity or 0) * mult
            # Capped loss in the position's currency
            capped_loss_native = cost * (threshold_pct / 100.0)
            capped_loss_usd = get_pnl_in_usd(
                type("X", (), {"net_pnl": capped_loss_native, "currency": p.currency})
            )
            counter_by_m[m] += capped_loss_usd
            capped.append(p.id)
        else:
            counter_by_m[m] += pnl_usd

    all_months = sorted(set(actual_by_m.keys()) | set(counter_by_m.keys()))
    actual_total = sum(actual_by_m.values())
    counter_total = sum(counter_by_m.values())

    monthly_rows: List[Dict] = []
    cum_a = 0.0
    cum_c = 0.0
    for m in all_months:
        a = round(actual_by_m.get(m, 0.0), 2)
        c = round(counter_by_m.get(m, 0.0), 2)
        cum_a += a
        cum_c += c
        monthly_rows.append({
            "month": m,
            "actual_pnl": a,
            "cf_pnl": c,
            "savings": round(c - a, 2),
            "actual_cumulative": round(cum_a, 2),
            "cf_cumulative": round(cum_c, 2),
        })

    by_sym: Dict[str, int] = defaultdict(int)
    capped_set = set(capped)
    for p in positions:
        if p.id in capped_set:
            by_sym[p.symbol] += 1

    return RuleResult(
        rule_id=f"cf5_hard_stop_{int(abs(threshold_pct))}pct",
        params={"threshold_pct": threshold_pct},
        skipped_position_ids=capped,
        skipped_count=len(capped),
        actual_total_pnl=round(actual_total, 2),
        counterfactual_total_pnl=round(counter_total, 2),
        savings=round(counter_total - actual_total, 2),
        monthly=monthly_rows,
        skipped_by_symbol=dict(by_sym),
        notes=(
            f"对任何亏损超过 {threshold_pct}% 的仓位，假设当时严格止损在 "
            f"{threshold_pct}%。命中 {len(capped)} 笔。"
        ),
        notes_en=(
            f"For any position that lost more than {threshold_pct}%, assume a hard "
            f"stop at {threshold_pct}%. {len(capped)} positions affected."
        ),
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RULES: Dict[str, RuleConfig] = {
    "cf1_consec_loss": RuleConfig(
        rule_id="cf1_consec_loss",
        name_cn="连亏熔断",
        name_en="Consecutive-loss cutoff",
        description_cn="同一标的连续 N 笔亏损后，跳过后续所有该标的的交易",
        description_en="After N consecutive losses on a ticker, skip all subsequent trades on it",
        default_params={"n_losses": 3},
        apply=cf1_consecutive_loss_cutoff,
    ),
    "cf2_no_revenge": RuleConfig(
        rule_id="cf2_no_revenge",
        name_cn="反报复交易",
        name_en="No revenge trading",
        description_cn="亏损平仓后 N 小时内的新开仓视为报复性交易，跳过",
        description_en="Trades opened within N hours of a losing close are skipped as revenge trades",
        default_params={"cooldown_hours": 2.0},
        apply=cf2_no_revenge_trading,
    ),
    "cf3_avoid_losers": RuleConfig(
        rule_id="cf3_avoid_losers",
        name_cn="规避长期亏损标的",
        name_en="Avoid persistent losers",
        description_cn="完全避开全期胜率 < X% 且总盈亏 < 0 的标的",
        description_en="Skip all trades on tickers with full-period win rate < X% and negative total P&L",
        default_params={"min_trades": 5, "max_win_rate": 0.40},
        apply=cf3_avoid_persistent_losers,
    ),
    "cf4_size_cap": RuleConfig(
        rule_id="cf4_size_cap",
        name_cn="仓位管理上限",
        name_en="Position-size cap",
        description_cn="单笔仓位金额超过历史中位数 N× 时按比例缩小",
        description_en="Cap any single position to N× the rolling-median size at opening time",
        default_params={"cap_multiple": 3.0},
        apply=cf4_position_size_cap,
    ),
    "cf5_hard_stop": RuleConfig(
        rule_id="cf5_hard_stop",
        name_cn="严格止损 -X%",
        name_en="Hard stop-loss at -X%",
        description_cn="任何亏损超过 -X% 的仓位假设按 -X% 止损",
        description_en="Cap any loss exceeding -X% to -X% of cost basis",
        default_params={"threshold_pct": -10.0},
        apply=cf5_hard_stop_loss,
    ),
}


def run_rule(
    positions: List[Position], rule_id: str, params: Optional[Dict] = None
) -> RuleResult:
    if rule_id not in RULES:
        raise ValueError(f"Unknown counterfactual rule: {rule_id}")
    cfg = RULES[rule_id]
    final_params = {**cfg.default_params, **(params or {})}
    return cfg.apply(positions, final_params)


def run_all_rules(positions: List[Position]) -> List[RuleResult]:
    """Run every rule with default params; useful for the summary view."""
    return [run_rule(positions, rid) for rid in RULES.keys()]
