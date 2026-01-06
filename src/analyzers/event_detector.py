"""
EventDetector - 事件检测器

input: Position, MarketData, yfinance财报日历
output: EventContext记录（财报/异常/宏观事件）
pos: 分析器层 - 检测持仓期间的重大事件并计算市场反应

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

功能:
1. 从 yfinance 获取财报日历
2. 检测价格/成交量异常作为未知事件代理
3. 将持仓与事件按日期匹配
4. 计算事件影响指标（价格变动、成交量激增等）
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.models.event_context import EventContext

logger = logging.getLogger(__name__)

# 配置参数
PRICE_CHANGE_THRESHOLD = 0.05      # 5% 视为价格异常
VOLUME_SPIKE_THRESHOLD = 2.0       # 2倍均量视为成交量异常
GAP_THRESHOLD = 0.03               # 3% 跳空视为异常
LOOKBACK_DAYS = 20                 # 计算均值的回看天数


class EventDetector:
    """事件检测器"""

    def __init__(self, session: Session):
        self.session = session

    # ========================================================================
    # 财报日历获取
    # ========================================================================

    def fetch_earnings_calendar(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> list[dict]:
        """
        从 yfinance 获取财报日历

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            财报事件列表 [{date, type, surprise_pct, eps_actual, eps_estimate}]
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)

            # 获取财报日历
            calendar = ticker.calendar
            earnings_dates = ticker.earnings_dates

            events = []

            if earnings_dates is not None and not earnings_dates.empty:
                for idx, row in earnings_dates.iterrows():
                    event_date = idx.date() if hasattr(idx, 'date') else idx

                    if start_date <= event_date <= end_date:
                        eps_actual = row.get('Reported EPS')
                        eps_estimate = row.get('EPS Estimate')
                        surprise_pct = row.get('Surprise(%)')

                        # 判断是否超预期
                        is_surprise = False
                        surprise_direction = None
                        if eps_actual is not None and eps_estimate is not None:
                            try:
                                if float(eps_actual) > float(eps_estimate):
                                    is_surprise = True
                                    surprise_direction = 'beat'
                                elif float(eps_actual) < float(eps_estimate):
                                    is_surprise = True
                                    surprise_direction = 'miss'
                            except (ValueError, TypeError):
                                pass

                        events.append({
                            'event_type': 'earnings',
                            'event_date': event_date,
                            'event_title': f"{symbol} 财报发布",
                            'is_surprise': is_surprise,
                            'surprise_direction': surprise_direction,
                            'surprise_magnitude': float(surprise_pct) if surprise_pct else None,
                            'source': 'yfinance',
                            'source_data': {
                                'eps_actual': float(eps_actual) if eps_actual else None,
                                'eps_estimate': float(eps_estimate) if eps_estimate else None,
                            }
                        })

            return events

        except Exception as e:
            logger.warning(f"获取 {symbol} 财报日历失败: {e}")
            return []

    # ========================================================================
    # 价格/成交量异常检测
    # ========================================================================

    def detect_price_anomalies(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        price_threshold: float = PRICE_CHANGE_THRESHOLD,
        volume_threshold: float = VOLUME_SPIKE_THRESHOLD,
        gap_threshold: float = GAP_THRESHOLD
    ) -> list[dict]:
        """
        检测价格和成交量异常

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            price_threshold: 价格变动阈值
            volume_threshold: 成交量激增阈值
            gap_threshold: 跳空阈值

        Returns:
            异常事件列表
        """
        events = []

        # 获取市场数据（包含回看期）
        lookback_start = start_date - timedelta(days=LOOKBACK_DAYS + 10)

        market_data = self.session.query(MarketData).filter(
            and_(
                MarketData.symbol == symbol,
                MarketData.timestamp >= lookback_start,
                MarketData.timestamp <= end_date + timedelta(days=1)
            )
        ).order_by(MarketData.timestamp).all()

        if len(market_data) < LOOKBACK_DAYS:
            logger.debug(f"{symbol} 市场数据不足，跳过异常检测")
            return events

        # 构建数据映射
        data_by_date = {}
        for md in market_data:
            md_date = md.timestamp.date() if hasattr(md.timestamp, 'date') else md.timestamp
            data_by_date[md_date] = md

        # 遍历检测日期范围
        current = start_date
        while current <= end_date:
            if current not in data_by_date:
                current += timedelta(days=1)
                continue

            today = data_by_date[current]

            # 获取前一日数据
            prev_date = current - timedelta(days=1)
            attempts = 0
            while prev_date not in data_by_date and attempts < 5:
                prev_date -= timedelta(days=1)
                attempts += 1

            if prev_date not in data_by_date:
                current += timedelta(days=1)
                continue

            yesterday = data_by_date[prev_date]

            # 计算价格变动
            if yesterday.close and today.close:
                price_change_pct = (float(today.close) - float(yesterday.close)) / float(yesterday.close)

                # 检测大幅价格变动
                if abs(price_change_pct) >= price_threshold:
                    impact = 'positive' if price_change_pct > 0 else 'negative'
                    events.append({
                        'event_type': 'price_anomaly',
                        'event_date': current,
                        'event_title': f"{symbol} 价格异动 {price_change_pct*100:+.1f}%",
                        'event_impact': impact,
                        'event_importance': min(10, int(abs(price_change_pct) * 100)),
                        'price_before': float(yesterday.close),
                        'price_after': float(today.close),
                        'price_change': float(today.close) - float(yesterday.close),
                        'price_change_pct': price_change_pct * 100,
                        'event_day_high': float(today.high) if today.high else None,
                        'event_day_low': float(today.low) if today.low else None,
                        'source': 'detected',
                        'confidence': 80,
                    })

            # 检测跳空
            if yesterday.close and today.open:
                gap_pct = (float(today.open) - float(yesterday.close)) / float(yesterday.close)

                if abs(gap_pct) >= gap_threshold:
                    impact = 'positive' if gap_pct > 0 else 'negative'
                    # 避免与价格异常重复
                    existing = [e for e in events if e['event_date'] == current and e['event_type'] == 'price_anomaly']
                    if not existing:
                        events.append({
                            'event_type': 'price_anomaly',
                            'event_date': current,
                            'event_title': f"{symbol} 跳空 {gap_pct*100:+.1f}%",
                            'event_impact': impact,
                            'event_importance': min(8, int(abs(gap_pct) * 100)),
                            'gap_pct': gap_pct * 100,
                            'price_before': float(yesterday.close),
                            'price_after': float(today.close) if today.close else None,
                            'source': 'detected',
                            'confidence': 75,
                        })

            # 计算成交量异常
            if today.volume:
                # 计算20日均量
                volume_dates = []
                check_date = current - timedelta(days=1)
                while len(volume_dates) < LOOKBACK_DAYS and check_date >= lookback_start:
                    if check_date in data_by_date and data_by_date[check_date].volume:
                        volume_dates.append(float(data_by_date[check_date].volume))
                    check_date -= timedelta(days=1)

                if len(volume_dates) >= 10:
                    avg_volume = sum(volume_dates) / len(volume_dates)
                    volume_ratio = float(today.volume) / avg_volume if avg_volume > 0 else 1

                    if volume_ratio >= volume_threshold:
                        # 成交量激增
                        events.append({
                            'event_type': 'volume_anomaly',
                            'event_date': current,
                            'event_title': f"{symbol} 成交量激增 {volume_ratio:.1f}x",
                            'event_importance': min(7, int(volume_ratio)),
                            'volume_on_event': float(today.volume),
                            'volume_avg_20d': avg_volume,
                            'volume_spike': volume_ratio,
                            'source': 'detected',
                            'confidence': 70,
                        })

            current += timedelta(days=1)

        return events

    # ========================================================================
    # 持仓事件关联
    # ========================================================================

    def detect_events_for_position(
        self,
        position: Position,
        include_earnings: bool = True,
        include_anomalies: bool = True
    ) -> list[dict]:
        """
        检测持仓期间的所有事件

        Args:
            position: 持仓记录
            include_earnings: 是否包含财报事件
            include_anomalies: 是否包含异常事件

        Returns:
            事件列表
        """
        symbol = position.underlying_symbol if position.is_option else position.symbol
        start_date = position.open_date
        end_date = position.close_date or date.today()

        # 扩展日期范围以捕获事件前后影响
        search_start = start_date - timedelta(days=5)
        search_end = end_date + timedelta(days=5)

        all_events = []

        # 获取财报事件
        if include_earnings:
            earnings_events = self.fetch_earnings_calendar(symbol, search_start, search_end)
            all_events.extend(earnings_events)

        # 检测异常事件
        if include_anomalies:
            anomaly_events = self.detect_price_anomalies(symbol, start_date, end_date)
            all_events.extend(anomaly_events)

        # 按日期排序
        all_events.sort(key=lambda x: x['event_date'])

        # 补充持仓影响信息
        for event in all_events:
            event['symbol'] = symbol
            event['position_id'] = position.id

            # 计算事件日的持仓盈亏（如果有市场数据）
            self._calculate_position_impact(position, event)

        return all_events

    def _calculate_position_impact(self, position: Position, event: dict):
        """计算事件对持仓的影响"""
        event_date = event['event_date']
        symbol = event.get('symbol', position.symbol)

        # 获取事件日收盘价
        md = self.session.query(MarketData).filter(
            and_(
                MarketData.symbol == symbol,
                MarketData.timestamp >= datetime.combine(event_date, datetime.min.time()),
                MarketData.timestamp < datetime.combine(event_date + timedelta(days=1), datetime.min.time())
            )
        ).first()

        if md and md.close and position.open_price:
            # 计算事件日盈亏
            multiplier = 100 if position.is_option else 1

            if position.direction == 'long':
                pnl = (float(md.close) - float(position.open_price)) * position.quantity * multiplier
            else:
                pnl = (float(position.open_price) - float(md.close)) * position.quantity * multiplier

            cost_basis = float(position.open_price) * position.quantity * multiplier
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

            event['position_pnl_on_event'] = pnl
            event['position_pnl_pct_on_event'] = pnl_pct

    # ========================================================================
    # 保存事件到数据库
    # ========================================================================

    def save_events(self, events: list[dict], deduplicate: bool = True) -> int:
        """
        保存事件到数据库

        Args:
            events: 事件列表
            deduplicate: 是否去重

        Returns:
            保存的事件数量
        """
        saved = 0

        for event_data in events:
            # 生成事件组ID（用于去重）
            event_key = f"{event_data.get('symbol')}_{event_data.get('event_date')}_{event_data.get('event_type')}"
            event_group_id = hashlib.md5(event_key.encode()).hexdigest()[:16]

            # 检查是否已存在
            if deduplicate:
                existing = self.session.query(EventContext).filter(
                    and_(
                        EventContext.symbol == event_data.get('symbol'),
                        EventContext.event_date == event_data.get('event_date'),
                        EventContext.event_type == event_data.get('event_type'),
                        EventContext.position_id == event_data.get('position_id')
                    )
                ).first()

                if existing:
                    continue

            # 创建事件记录
            event = EventContext(
                position_id=event_data.get('position_id'),
                symbol=event_data.get('symbol'),
                underlying_symbol=event_data.get('underlying_symbol'),
                event_type=event_data.get('event_type'),
                event_date=event_data.get('event_date'),
                event_time=event_data.get('event_time'),
                event_title=event_data.get('event_title'),
                event_description=event_data.get('event_description'),
                event_impact=event_data.get('event_impact', 'unknown'),
                event_importance=event_data.get('event_importance', 5),
                is_surprise=event_data.get('is_surprise', False),
                surprise_direction=event_data.get('surprise_direction'),
                surprise_magnitude=event_data.get('surprise_magnitude'),
                price_before=event_data.get('price_before'),
                price_after=event_data.get('price_after'),
                price_change=event_data.get('price_change'),
                price_change_pct=event_data.get('price_change_pct'),
                event_day_high=event_data.get('event_day_high'),
                event_day_low=event_data.get('event_day_low'),
                volume_on_event=event_data.get('volume_on_event'),
                volume_avg_20d=event_data.get('volume_avg_20d'),
                volume_spike=event_data.get('volume_spike'),
                gap_pct=event_data.get('gap_pct'),
                position_pnl_on_event=event_data.get('position_pnl_on_event'),
                position_pnl_pct_on_event=event_data.get('position_pnl_pct_on_event'),
                source=event_data.get('source'),
                source_data=event_data.get('source_data'),
                confidence=event_data.get('confidence', 100),
                event_group_id=event_group_id,
            )

            self.session.add(event)
            saved += 1

        if saved > 0:
            self.session.commit()

        return saved

    # ========================================================================
    # 批量处理
    # ========================================================================

    def detect_events_for_all_positions(
        self,
        status: PositionStatus = PositionStatus.CLOSED,
        limit: Optional[int] = None,
        skip_existing: bool = True
    ) -> dict:
        """
        为所有持仓检测事件

        Args:
            status: 持仓状态过滤
            limit: 最大处理数量
            skip_existing: 跳过已有事件的持仓

        Returns:
            处理统计 {processed, events_found, events_saved}
        """
        query = self.session.query(Position).filter(Position.status == status)

        if skip_existing:
            # 获取已有事件的持仓ID
            existing_ids = self.session.query(EventContext.position_id).distinct().all()
            existing_ids = [r[0] for r in existing_ids if r[0]]
            if existing_ids:
                query = query.filter(~Position.id.in_(existing_ids))

        if limit:
            query = query.limit(limit)

        positions = query.all()

        stats = {
            'processed': 0,
            'events_found': 0,
            'events_saved': 0,
        }

        for position in positions:
            try:
                events = self.detect_events_for_position(position)
                stats['events_found'] += len(events)

                if events:
                    saved = self.save_events(events)
                    stats['events_saved'] += saved

                stats['processed'] += 1

                if stats['processed'] % 10 == 0:
                    logger.info(f"已处理 {stats['processed']} 个持仓，发现 {stats['events_found']} 个事件")

            except Exception as e:
                logger.error(f"处理持仓 {position.id} 失败: {e}")

        logger.info(f"事件检测完成: 处理 {stats['processed']} 个持仓，"
                   f"发现 {stats['events_found']} 个事件，保存 {stats['events_saved']} 个")

        return stats

    # ========================================================================
    # 查询接口
    # ========================================================================

    def get_events_for_position(self, position_id: int) -> list[EventContext]:
        """获取持仓关联的所有事件"""
        return self.session.query(EventContext).filter(
            EventContext.position_id == position_id
        ).order_by(EventContext.event_date).all()

    def get_high_impact_events(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_importance: int = 7
    ) -> list[EventContext]:
        """获取高影响事件"""
        query = self.session.query(EventContext).filter(
            EventContext.event_importance >= min_importance
        )

        if symbol:
            query = query.filter(EventContext.symbol == symbol)
        if start_date:
            query = query.filter(EventContext.event_date >= start_date)
        if end_date:
            query = query.filter(EventContext.event_date <= end_date)

        return query.order_by(EventContext.event_date.desc()).all()

    def get_events_by_type(
        self,
        event_type: str,
        limit: int = 50
    ) -> list[EventContext]:
        """按类型获取事件"""
        return self.session.query(EventContext).filter(
            EventContext.event_type == event_type
        ).order_by(EventContext.event_date.desc()).limit(limit).all()

    def get_event_statistics(self) -> dict:
        """获取事件统计"""
        from sqlalchemy import func

        total = self.session.query(func.count(EventContext.id)).scalar() or 0

        by_type = self.session.query(
            EventContext.event_type,
            func.count(EventContext.id)
        ).group_by(EventContext.event_type).all()

        by_impact = self.session.query(
            EventContext.event_impact,
            func.count(EventContext.id)
        ).group_by(EventContext.event_impact).all()

        return {
            'total_events': total,
            'by_type': {t: c for t, c in by_type},
            'by_impact': {i: c for i, c in by_impact if i},
        }
