"""
Unit tests for the rule-based insight engine.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.services.insight_engine import InsightEngine
from src.models.base import Base
from src.models.position import Position, PositionStatus


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _add_closed_position(session, symbol: str, close_day: date, net_pnl: float):
    position = Position(
        symbol=symbol,
        symbol_name=symbol,
        direction="long",
        status=PositionStatus.CLOSED,
        open_time=datetime(close_day.year, close_day.month, close_day.day, 9, 30),
        close_time=datetime(close_day.year, close_day.month, close_day.day, 16, 0),
        open_date=close_day,
        close_date=close_day,
        holding_period_days=0,
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
        assert insight.data_points["affected_symbols"] == 3
        assert insight.data_points["max_consecutive_losses"] == 5
        assert "CCC" in insight.data_points["symbols"]
    finally:
        session.close()
