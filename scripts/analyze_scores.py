#!/usr/bin/env python3
"""
分析交易质量评分结果
"""
import sys
sys.path.insert(0, '.')
from src.models.base import init_database, get_session
from src.models.position import Position, PositionStatus
from sqlalchemy import func
import config

engine = init_database(config.DATABASE_URL, echo=False)
session = get_session()

# 按股票符号统计
print('='*80)
print('按股票符号统计（前15名）')
print('='*80)
symbol_stats = session.query(
    Position.symbol,
    func.count(Position.id).label('count'),
    func.avg(Position.overall_score).label('avg_score'),
    func.sum(Position.realized_pnl).label('total_pnl')
).filter(
    Position.status == PositionStatus.CLOSED,
    Position.overall_score.isnot(None)
).group_by(Position.symbol).order_by(func.sum(Position.realized_pnl).desc()).limit(15).all()

print(f"{'Symbol':<10} {'Count':>6} {'Avg Score':>10} {'Total PnL':>12}")
print('-'*80)
for symbol, count, avg_score, total_pnl in symbol_stats:
    print(f'{symbol:<10} {count:>6} {avg_score:>10.1f} ${total_pnl:>11.2f}')

# 盈利vs亏损统计
print('\n' + '='*80)
print('盈利 vs 亏损统计')
print('='*80)
profit_positions = session.query(Position).filter(
    Position.status == PositionStatus.CLOSED,
    Position.realized_pnl > 0,
    Position.overall_score.isnot(None)
).all()

loss_positions = session.query(Position).filter(
    Position.status == PositionStatus.CLOSED,
    Position.realized_pnl < 0,
    Position.overall_score.isnot(None)
).all()

print(f'盈利交易: {len(profit_positions)} ({len(profit_positions)/1324*100:.1f}%)')
print(f'  平均评分: {sum(p.overall_score for p in profit_positions)/len(profit_positions):.1f}')
print(f'  总盈利: ${sum(p.realized_pnl for p in profit_positions):.2f}')
print(f'\n亏损交易: {len(loss_positions)} ({len(loss_positions)/1324*100:.1f}%)')
print(f'  平均评分: {sum(p.overall_score for p in loss_positions)/len(loss_positions):.1f}')
print(f'  总亏损: ${sum(p.realized_pnl for p in loss_positions):.2f}')

total_pnl = sum(p.realized_pnl for p in profit_positions) + sum(p.realized_pnl for p in loss_positions)
print(f'\n净盈亏: ${total_pnl:.2f}')
win_rate = len(profit_positions) / (len(profit_positions) + len(loss_positions)) * 100
print(f'胜率: {win_rate:.1f}%')

# 评分等级与盈利关系
print('\n' + '='*80)
print('评分等级与盈利率关系')
print('='*80)
grades = ['B', 'B-', 'C+', 'C', 'C-', 'D']
print(f"{'Grade':<6} {'Count':>6} {'Win Rate':>10} {'Avg PnL':>12}")
print('-'*80)
for grade in grades:
    grade_positions = session.query(Position).filter(
        Position.status == PositionStatus.CLOSED,
        Position.score_grade == grade
    ).all()

    if grade_positions:
        win_count = len([p for p in grade_positions if p.realized_pnl > 0])
        win_rate = win_count / len(grade_positions) * 100
        avg_pnl = sum(p.realized_pnl for p in grade_positions) / len(grade_positions)
        print(f'{grade:<6} {len(grade_positions):>6} {win_rate:>9.1f}% ${avg_pnl:>11.2f}')

# 最佳和最差交易
print('\n' + '='*80)
print('最佳交易（评分最高）')
print('='*80)
best_trades = session.query(Position).filter(
    Position.status == PositionStatus.CLOSED,
    Position.overall_score.isnot(None)
).order_by(Position.overall_score.desc()).limit(5).all()

print(f"{'ID':<6} {'Symbol':<10} {'Grade':<6} {'Score':>6} {'PnL':>10} {'Days':>5}")
print('-'*80)
for pos in best_trades:
    print(f'{pos.id:<6} {pos.symbol:<10} {pos.score_grade:<6} {pos.overall_score:>6.1f} ${pos.realized_pnl:>9.2f} {pos.holding_period_days:>5}')

print('\n' + '='*80)
print('最差交易（评分最低）')
print('='*80)
worst_trades = session.query(Position).filter(
    Position.status == PositionStatus.CLOSED,
    Position.overall_score.isnot(None)
).order_by(Position.overall_score.asc()).limit(5).all()

print(f"{'ID':<6} {'Symbol':<10} {'Grade':<6} {'Score':>6} {'PnL':>10} {'Days':>5}")
print('-'*80)
for pos in worst_trades:
    print(f'{pos.id:<6} {pos.symbol:<10} {pos.score_grade:<6} {pos.overall_score:>6.1f} ${pos.realized_pnl:>9.2f} {pos.holding_period_days:>5}')

session.close()
