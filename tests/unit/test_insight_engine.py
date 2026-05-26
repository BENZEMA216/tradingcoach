"""
Unit tests for the rule-based insight engine.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.schemas.insights import InsightType
from backend.app.services.insight_engine import InsightEngine
from src.models.base import Base
from src.models.position import Position, PositionStatus


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _add_closed_position(
    session,
    symbol: str,
    close_day: date,
    net_pnl: float,
    holding_days: int = 0,
):
    open_day = close_day - timedelta(days=holding_days)
    position = Position(
        symbol=symbol,
        symbol_name=symbol,
        direction="long",
        status=PositionStatus.CLOSED,
        open_time=datetime(open_day.year, open_day.month, open_day.day, 9, 30),
        close_time=datetime(close_day.year, close_day.month, close_day.day, 16, 0),
        open_date=open_day,
        close_date=close_day,
        holding_period_days=holding_days,
        open_price=100,
        close_price=101,
        quantity=1,
        realized_pnl=net_pnl,
        net_pnl=net_pnl,
        total_fees=0,
        market="美股",
        currency="USD",
    )
    session.add(position)


def test_repeated_symbol_loss_insights_are_aggregated():
    session = _make_session()
    start = date(2025, 1, 1)

    try:
        symbol_pnls = {
            "AAA": [-10, -20, -30, -40, 50],
            "BBB": [-10, -20, -30, 40, 50],
            "CCC": [-10, -20, -30, -40, -50],
        }
        offset = 0
        for symbol, pnls in symbol_pnls.items():
            for pnl in pnls:
                _add_closed_position(session, symbol, start + timedelta(days=offset), pnl)
                offset += 1
        session.commit()

        insights = InsightEngine(session).generate_insights(limit=20)

        repeated_loss_insights = [
            insight for insight in insights if insight.id.startswith("S04")
        ]
        assert len(repeated_loss_insights) == 1

        insight = repeated_loss_insights[0]
        assert insight.id == "S04A"
        assert insight.type == InsightType.REMINDER
        assert insight.data_points["affected_symbols"] == 3
        assert insight.data_points["max_consecutive_losses"] == 5
        assert "CCC" in insight.data_points["symbols"]
    finally:
        session.close()


def test_poor_symbol_performance_is_not_a_global_insight():
    session = _make_session()
    start = date(2025, 1, 1)

    try:
        for index in range(6):
            _add_closed_position(session, "WEAK", start + timedelta(days=index), -100)
        session.commit()

        insights = InsightEngine(session).generate_insights(limit=30)

        assert not any(insight.id == "S02-WEAK" for insight in insights)
    finally:
        session.close()


def test_weekly_loss_insight_uses_unique_rule_id():
    session = _make_session()
    start = date(2025, 1, 6)

    try:
        for index in range(10):
            _add_closed_position(
                session,
                "AAA",
                start + timedelta(days=index * 2),
                -100,
            )
        session.commit()

        insights = InsightEngine(session).generate_insights(limit=30)

        weekly_loss_insights = [
            insight for insight in insights if insight.data_points.get("weeks_negative") == 3
        ]
        assert len(weekly_loss_insights) == 1

        insight = weekly_loss_insights[0]
        assert insight.id == "P02-weekly"
        assert insight.type == InsightType.REMINDER
        assert insight.title == "连续3周亏损"
        assert insight.data_points["total_loss"] == -1000
        assert insight.data_points["total_loss_display"] == "1,000"
        assert not any(
            item.id == "P02" and item.data_points.get("weeks_negative") == 3
            for item in insights
        )
    finally:
        session.close()


def test_performance_decline_insight_is_a_reminder_not_a_problem():
    session = _make_session()
    start = date(2025, 3, 3)

    try:
        for index in range(5):
            _add_closed_position(session, "AAA", start + timedelta(days=index), 100)
        for index in range(5):
            _add_closed_position(session, "BBB", start + timedelta(days=7 + index), -100)
        session.commit()

        insights = InsightEngine(session).generate_insights(limit=30)

        insight = next(item for item in insights if item.id == "P02")
        assert insight.type == InsightType.REMINDER
        assert insight.title == "近期表现下滑"
        assert insight.data_points["early_win_rate"] == 100.0
        assert insight.data_points["recent_win_rate"] == 0.0
    finally:
        session.close()


def test_holding_style_insight_includes_i18n_variables():
    session = _make_session()
    start = date(2025, 2, 3)

    try:
        for index in range(5):
            _add_closed_position(session, "DAY", start + timedelta(days=index), 100)
        for index in range(5):
            _add_closed_position(
                session,
                "SWING",
                start + timedelta(days=7 + index),
                -100,
                holding_days=2,
            )
        session.commit()

        insights = InsightEngine(session).generate_insights(limit=30)

        insight = next(item for item in insights if item.id == "H03")
        assert insight.title == "日内交易更擅长"
        assert insight.data_points["better"] == "日内"
        assert insight.data_points["worse"] == "波段"
        assert insight.data_points["better_style"] == "intraday"
        assert insight.data_points["worse_style"] == "swing"
        assert insight.data_points["better_wr"] == 100.0
        assert insight.data_points["worse_wr"] == 0.0
    finally:
        session.close()
