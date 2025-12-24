#!/usr/bin/env python3
"""
input: data/tradingcoach.db
output: 修复后的数据库
pos: 数据完整性修复脚本

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

修复项目:
1. DI-POS-012: 期权字段缺失 - 从 symbol 解析 option_type/strike_price/expiry_date
2. DI-POS-011: 评分等级不匹配 - 重新计算 score_grade
"""
import re
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_PATH


def parse_option_symbol(symbol: str) -> dict:
    """
    解析期权符号，提取期权信息

    格式示例:
    - NVDA250207C120000 -> NVDA, 2025-02-07, CALL, 120.00
    - TSLA250307P395000 -> TSLA, 2025-03-07, PUT, 395.00
    - PLTR250228P100000 -> PLTR, 2025-02-28, PUT, 100.00
    """
    # 标准期权符号格式: SYMBOL + YYMMDD + C/P + STRIKE(带小数点偏移)
    pattern = r'^([A-Z]+)(\d{6})([CP])(\d+)$'
    match = re.match(pattern, symbol)

    if not match:
        return None

    underlying = match.group(1)
    date_str = match.group(2)  # YYMMDD
    option_type_char = match.group(3)
    strike_raw = match.group(4)

    # 解析日期 (YYMMDD -> YYYY-MM-DD)
    try:
        year = 2000 + int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
        expiry_date = f"{year:04d}-{month:02d}-{day:02d}"
    except ValueError:
        return None

    # 解析期权类型
    option_type = 'CALL' if option_type_char == 'C' else 'PUT'

    # 解析行权价 (通常最后3位是小数部分)
    # 例如 120000 -> 120.000, 395000 -> 395.000
    strike_price = int(strike_raw) / 1000.0

    return {
        'underlying_symbol': underlying,
        'expiry_date': expiry_date,
        'option_type': option_type,
        'strike_price': strike_price
    }


def fix_option_fields(session):
    """
    修复 DI-POS-012: 期权持仓字段缺失
    从 symbol 解析 option_type/strike_price/expiry_date
    """
    print("\n=== 修复期权字段缺失 (DI-POS-012) ===")

    # 查询需要修复的记录
    result = session.execute(text("""
        SELECT id, symbol FROM positions
        WHERE is_option = 1
          AND (option_type IS NULL OR strike_price IS NULL OR expiry_date IS NULL)
    """)).fetchall()

    if not result:
        print("没有需要修复的期权记录")
        return 0

    print(f"发现 {len(result)} 条需要修复的期权记录")

    fixed_count = 0
    failed_symbols = []

    for row in result:
        pos_id, symbol = row
        parsed = parse_option_symbol(symbol)

        if parsed:
            session.execute(text("""
                UPDATE positions
                SET option_type = :option_type,
                    strike_price = :strike_price,
                    expiry_date = :expiry_date,
                    underlying_symbol = :underlying_symbol
                WHERE id = :id
            """), {
                'id': pos_id,
                'option_type': parsed['option_type'],
                'strike_price': parsed['strike_price'],
                'expiry_date': parsed['expiry_date'],
                'underlying_symbol': parsed['underlying_symbol']
            })
            fixed_count += 1
        else:
            failed_symbols.append((pos_id, symbol))

    if failed_symbols:
        print(f"无法解析的符号 ({len(failed_symbols)} 条):")
        for pos_id, symbol in failed_symbols[:5]:
            print(f"  - ID {pos_id}: {symbol}")
        if len(failed_symbols) > 5:
            print(f"  ... 还有 {len(failed_symbols) - 5} 条")

    print(f"成功修复: {fixed_count} 条")
    return fixed_count


def fix_score_grade(session):
    """
    修复 DI-POS-011: 评分等级与分数不匹配
    重新计算 score_grade
    """
    print("\n=== 修复评分等级不匹配 (DI-POS-011) ===")

    # 查询不匹配的记录
    result = session.execute(text("""
        SELECT id, symbol, overall_score, score_grade FROM positions
        WHERE overall_score IS NOT NULL
          AND score_grade IS NOT NULL
          AND NOT (
            (overall_score >= 90 AND score_grade = 'A') OR
            (overall_score >= 80 AND overall_score < 90 AND score_grade = 'B') OR
            (overall_score >= 70 AND overall_score < 80 AND score_grade = 'C') OR
            (overall_score >= 60 AND overall_score < 70 AND score_grade = 'D') OR
            (overall_score < 60 AND score_grade = 'F')
          )
    """)).fetchall()

    if not result:
        print("没有需要修复的评分等级")
        return 0

    print(f"发现 {len(result)} 条评分等级不匹配")

    fixed_count = 0
    for row in result:
        pos_id, symbol, score, old_grade = row

        # 计算正确的等级
        if score >= 90:
            new_grade = 'A'
        elif score >= 80:
            new_grade = 'B'
        elif score >= 70:
            new_grade = 'C'
        elif score >= 60:
            new_grade = 'D'
        else:
            new_grade = 'F'

        print(f"  ID {pos_id} ({symbol}): {score:.2f} -> {old_grade} => {new_grade}")

        session.execute(text("""
            UPDATE positions SET score_grade = :grade WHERE id = :id
        """), {'id': pos_id, 'grade': new_grade})

        fixed_count += 1

    print(f"成功修复: {fixed_count} 条")
    return fixed_count


def analyze_trade_position_link(session):
    """
    分析 DI-MATCH-001: 已平仓持仓交易数不足
    """
    print("\n=== 分析交易-持仓关联问题 (DI-MATCH-001) ===")

    # 查询关联情况
    result = session.execute(text("""
        SELECT
            p.id, p.symbol, p.status, p.direction,
            COUNT(t.id) as trade_count,
            GROUP_CONCAT(t.direction) as trade_dirs
        FROM positions p
        LEFT JOIN trades t ON t.position_id = p.id
        WHERE p.status = 'CLOSED'
        GROUP BY p.id
        HAVING trade_count < 2
        LIMIT 20
    """)).fetchall()

    print(f"发现 {len(result)} 条已平仓持仓只有 1 笔交易 (前20条):")
    for row in result[:10]:
        print(f"  ID {row[0]}: {row[1]} ({row[3]}) - {row[4]} 笔交易 [{row[5]}]")

    # 查询这些持仓是否有对应的平仓交易未关联
    print("\n分析原因...")

    # 检查是否存在未关联的交易
    unlinked = session.execute(text("""
        SELECT COUNT(*) FROM trades WHERE position_id IS NULL
    """)).scalar()
    print(f"未关联到持仓的交易数: {unlinked}")

    # 检查交易总数和持仓关联情况
    stats = session.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM trades) as total_trades,
            (SELECT COUNT(*) FROM trades WHERE position_id IS NOT NULL) as linked_trades,
            (SELECT COUNT(*) FROM positions) as total_positions,
            (SELECT COUNT(*) FROM positions WHERE status = 'CLOSED') as closed_positions
    """)).fetchone()

    print(f"\n统计:")
    print(f"  总交易数: {stats[0]}")
    print(f"  已关联交易: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
    print(f"  总持仓数: {stats[2]}")
    print(f"  已平仓数: {stats[3]}")

    # 这个问题可能是业务逻辑设计：一个 position 只存储开仓交易的引用
    # 需要查看 FIFO matcher 的实现
    print("\n注意: 这可能是业务设计，需要查看 FIFO matcher 实现")
    print("建议: 检查 src/matchers/fifo_matcher.py 的 position_id 分配逻辑")


def main():
    print("=" * 60)
    print("数据完整性修复脚本")
    print(f"数据库: {DATABASE_PATH}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 连接数据库
    engine = create_engine(f"sqlite:///{DATABASE_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. 修复期权字段
        option_fixed = fix_option_fields(session)

        # 2. 修复评分等级
        grade_fixed = fix_score_grade(session)

        # 3. 分析交易关联问题
        analyze_trade_position_link(session)

        # 提交更改
        if option_fixed > 0 or grade_fixed > 0:
            session.commit()
            print("\n✅ 修复已提交到数据库")
        else:
            print("\n没有需要修复的数据")

        # 汇总
        print("\n" + "=" * 60)
        print("修复汇总:")
        print(f"  - 期权字段修复: {option_fixed} 条")
        print(f"  - 评分等级修复: {grade_fixed} 条")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\n❌ 修复失败: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
