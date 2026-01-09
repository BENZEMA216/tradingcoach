#!/usr/bin/env python3
"""
Data Quality Check - 综合数据质量监控脚本

input: 数据库, 股票代码, 日期范围
output: 数据质量报告 (JSON/Console)
pos: 运维脚本 - 整合新闻获取、股票数据、FIFO分析的质量监控

核心功能:
1. 数据库质量检查 - 交易/持仓数据完整性、一致性
2. 新闻获取验证 - DDGS 适配器可用性测试
3. 股票数据验证 - YFinance 数据源测试
4. FIFO 配对分析 - 配对结果质量检查

Usage:
    python scripts/data_quality_check.py                    # 完整检查
    python scripts/data_quality_check.py --quick            # 快速检查
    python scripts/data_quality_check.py --news AAPL        # 测试新闻获取
    python scripts/data_quality_check.py --stock AAPL       # 测试股票数据
    python scripts/data_quality_check.py --fifo             # FIFO 分析
    python scripts/data_quality_check.py --output report.json  # 输出到文件

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
import os
import json
import argparse
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataQualityChecker:
    """综合数据质量检查器"""

    def __init__(self, db_path: str = None):
        """
        初始化检查器

        Args:
            db_path: 数据库路径，默认使用配置
        """
        self.db_path = db_path or config.DATABASE_PATH
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "db_path": str(self.db_path),
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
            }
        }

    # =========================================================================
    # 1. 数据库质量检查
    # =========================================================================

    def check_database_quality(self) -> Dict[str, Any]:
        """
        检查数据库数据质量

        Returns:
            数据库质量报告
        """
        logger.info("=" * 60)
        logger.info("检查数据库质量...")
        logger.info("=" * 60)

        try:
            from src.validators.data_quality_monitor import DataQualityMonitor
            monitor = DataQualityMonitor(str(self.db_path))
            dashboard = monitor.generate_dashboard()

            result = {
                "status": "passed" if dashboard["summary"]["overall_score"] >= 70 else "failed",
                "health_status": dashboard["summary"]["health_status"],
                "overall_score": dashboard["summary"]["overall_score"],
                "total_records": dashboard["summary"]["total_records"],
                "anomalies": dashboard["summary"]["total_anomalies"],
                "critical_issues": dashboard["summary"]["critical_issues"],
                "tables": dashboard["tables"],
                "recommendations": dashboard["recommendations"],
            }

            self._log_check_result("database_quality", result)
            return result

        except Exception as e:
            logger.error(f"数据库质量检查失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    # =========================================================================
    # 2. 新闻获取验证
    # =========================================================================

    def check_news_fetcher(self, symbol: str = "AAPL") -> Dict[str, Any]:
        """
        测试新闻获取功能

        Args:
            symbol: 测试用的股票代码

        Returns:
            新闻获取测试结果
        """
        logger.info("=" * 60)
        logger.info(f"测试新闻获取 - {symbol}...")
        logger.info("=" * 60)

        try:
            from src.analyzers.news_adapters.ddgs_adapter import DDGSAdapter

            adapter = DDGSAdapter()

            # 检查可用性
            is_available = adapter.is_available()
            if not is_available:
                return {
                    "status": "failed",
                    "error": "DDGS 适配器不可用，请安装: pip install -U ddgs",
                    "is_available": False,
                }

            # 搜索新闻
            query = f"{symbol} stock news"
            search_date = date.today()
            news_results = adapter.search(query, search_date, days_range=7)

            result = {
                "status": "passed" if len(news_results) > 0 else "warning",
                "is_available": True,
                "adapter": "DDGS",
                "query": query,
                "results_count": len(news_results),
                "sample_results": news_results[:3] if news_results else [],
            }

            if len(news_results) == 0:
                result["warning"] = "未找到新闻结果，可能是查询限制或网络问题"

            self._log_check_result("news_fetcher", result)
            return result

        except ImportError as e:
            logger.error(f"导入 DDGS 适配器失败: {e}")
            return {
                "status": "failed",
                "error": f"请安装 ddgs: pip install -U ddgs - {e}",
                "is_available": False,
            }
        except Exception as e:
            logger.error(f"新闻获取测试失败: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # 3. 股票数据验证
    # =========================================================================

    def check_stock_data_fetcher(self, symbol: str = "AAPL") -> Dict[str, Any]:
        """
        测试股票数据获取功能

        Args:
            symbol: 测试用的股票代码

        Returns:
            股票数据测试结果
        """
        logger.info("=" * 60)
        logger.info(f"测试股票数据获取 - {symbol}...")
        logger.info("=" * 60)

        try:
            from src.data_sources.yfinance_client import YFinanceClient

            client = YFinanceClient()

            # 检查可用性
            is_available = client.is_available()

            # 获取 OHLCV 数据
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            try:
                df = client.get_ohlcv(symbol, start_date, end_date)
                ohlcv_success = True
                ohlcv_rows = len(df)
                ohlcv_columns = list(df.columns)
            except Exception as e:
                ohlcv_success = False
                ohlcv_rows = 0
                ohlcv_columns = []
                logger.warning(f"OHLCV 获取失败: {e}")

            # 获取股票信息
            try:
                stock_info = client.get_stock_info(symbol)
                info_success = True
                stock_name = stock_info.get('name', 'Unknown')
                current_price = stock_info.get('current_price')
            except Exception as e:
                info_success = False
                stock_name = None
                current_price = None
                logger.warning(f"股票信息获取失败: {e}")

            result = {
                "status": "passed" if (ohlcv_success and info_success) else "warning",
                "is_available": is_available,
                "data_source": "YFinance",
                "symbol": symbol,
                "ohlcv": {
                    "success": ohlcv_success,
                    "rows": ohlcv_rows,
                    "columns": ohlcv_columns,
                    "date_range": f"{start_date} to {end_date}",
                },
                "stock_info": {
                    "success": info_success,
                    "name": stock_name,
                    "current_price": current_price,
                },
            }

            if not ohlcv_success or not info_success:
                result["warning"] = "部分数据获取失败"

            self._log_check_result("stock_data_fetcher", result)
            return result

        except ImportError as e:
            logger.error(f"导入 YFinance 客户端失败: {e}")
            return {
                "status": "failed",
                "error": f"请安装 yfinance: pip install yfinance - {e}",
            }
        except Exception as e:
            logger.error(f"股票数据测试失败: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # 4. FIFO 配对分析
    # =========================================================================

    def check_fifo_matching(self) -> Dict[str, Any]:
        """
        检查 FIFO 配对质量

        Returns:
            FIFO 配对分析结果
        """
        logger.info("=" * 60)
        logger.info("分析 FIFO 配对质量...")
        logger.info("=" * 60)

        try:
            import sqlite3

            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. 交易统计
            cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'FILLED'")
            total_trades = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trades WHERE position_id IS NOT NULL")
            matched_trades = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trades WHERE position_id IS NULL AND status = 'FILLED'")
            unmatched_trades = cursor.fetchone()[0]

            # 2. 持仓统计
            cursor.execute("SELECT COUNT(*) FROM positions")
            total_positions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'CLOSED'")
            closed_positions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
            open_positions = cursor.fetchone()[0]

            # 3. 盈亏统计
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN net_pnl = 0 THEN 1 ELSE 0 END) as breakeven,
                    SUM(net_pnl) as total_pnl,
                    AVG(net_pnl) as avg_pnl
                FROM positions
                WHERE status = 'CLOSED' AND net_pnl IS NOT NULL
            """)
            pnl_stats = cursor.fetchone()

            wins = pnl_stats['wins'] or 0
            losses = pnl_stats['losses'] or 0
            total_closed = wins + losses + (pnl_stats['breakeven'] or 0)
            win_rate = (wins / total_closed * 100) if total_closed > 0 else 0

            # 4. 按标的统计
            cursor.execute("""
                SELECT symbol, COUNT(*) as count
                FROM positions
                GROUP BY symbol
                ORDER BY count DESC
                LIMIT 10
            """)
            top_symbols = [dict(row) for row in cursor.fetchall()]

            # 5. 检查配对一致性问题
            cursor.execute("""
                SELECT p.id, p.symbol, p.status,
                    (SELECT COUNT(*) FROM trades t WHERE t.position_id = p.id) as trade_count
                FROM positions p
                WHERE p.status = 'CLOSED'
                AND (SELECT COUNT(*) FROM trades t WHERE t.position_id = p.id) < 2
            """)
            inconsistent_positions = cursor.fetchall()

            conn.close()

            match_rate = (matched_trades / total_trades * 100) if total_trades > 0 else 0

            result = {
                "status": "passed" if match_rate >= 80 else "warning",
                "trades": {
                    "total": total_trades,
                    "matched": matched_trades,
                    "unmatched": unmatched_trades,
                    "match_rate": round(match_rate, 1),
                },
                "positions": {
                    "total": total_positions,
                    "closed": closed_positions,
                    "open": open_positions,
                },
                "performance": {
                    "wins": wins,
                    "losses": losses,
                    "win_rate": round(win_rate, 1),
                    "total_pnl": round(pnl_stats['total_pnl'] or 0, 2),
                    "avg_pnl": round(pnl_stats['avg_pnl'] or 0, 2),
                },
                "top_symbols": top_symbols,
                "issues": {
                    "inconsistent_positions": len(inconsistent_positions),
                }
            }

            if match_rate < 80:
                result["warning"] = f"配对率 {match_rate:.1f}% 低于 80%，建议重新运行配对"

            self._log_check_result("fifo_matching", result)
            return result

        except Exception as e:
            logger.error(f"FIFO 分析失败: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def _log_check_result(self, check_name: str, result: Dict[str, Any]):
        """记录检查结果"""
        self.results["checks"][check_name] = result
        self.results["summary"]["total_checks"] += 1

        status = result.get("status", "unknown")
        if status == "passed":
            self.results["summary"]["passed"] += 1
            logger.info(f"✓ {check_name}: PASSED")
        elif status == "warning":
            self.results["summary"]["warnings"] += 1
            logger.warning(f"⚠ {check_name}: WARNING - {result.get('warning', '')}")
        elif status == "failed":
            self.results["summary"]["failed"] += 1
            logger.error(f"✗ {check_name}: FAILED - {result.get('error', '')}")
        else:
            self.results["summary"]["failed"] += 1
            logger.error(f"✗ {check_name}: ERROR - {result.get('error', '')}")

    def run_all_checks(self, quick: bool = False) -> Dict[str, Any]:
        """
        运行所有检查

        Args:
            quick: 是否快速模式（跳过网络相关测试）

        Returns:
            完整的检查报告
        """
        logger.info("=" * 60)
        logger.info("开始综合数据质量检查")
        logger.info("=" * 60)

        # 1. 数据库质量检查（必选）
        self.results["checks"]["database"] = self.check_database_quality()

        # 2. FIFO 配对分析（必选）
        self.results["checks"]["fifo"] = self.check_fifo_matching()

        if not quick:
            # 3. 新闻获取测试
            self.results["checks"]["news"] = self.check_news_fetcher()

            # 4. 股票数据测试
            self.results["checks"]["stock"] = self.check_stock_data_fetcher()

        # 生成总结
        self._generate_summary()

        return self.results

    def _generate_summary(self):
        """生成检查总结"""
        summary = self.results["summary"]

        logger.info("\n" + "=" * 60)
        logger.info("检查总结")
        logger.info("=" * 60)
        logger.info(f"总检查项: {summary['total_checks']}")
        logger.info(f"通过: {summary['passed']}")
        logger.info(f"警告: {summary['warnings']}")
        logger.info(f"失败: {summary['failed']}")

        # 总体状态
        if summary['failed'] > 0:
            self.results["overall_status"] = "FAILED"
            logger.error("总体状态: FAILED")
        elif summary['warnings'] > 0:
            self.results["overall_status"] = "WARNING"
            logger.warning("总体状态: WARNING")
        else:
            self.results["overall_status"] = "PASSED"
            logger.info("总体状态: PASSED")

        logger.info("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="TradingCoach 数据质量监控工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/data_quality_check.py                    # 完整检查
  python scripts/data_quality_check.py --quick            # 快速检查（跳过网络测试）
  python scripts/data_quality_check.py --news NVDA        # 测试新闻获取
  python scripts/data_quality_check.py --stock TSLA       # 测试股票数据
  python scripts/data_quality_check.py --fifo             # FIFO 分析
  python scripts/data_quality_check.py --output report.json  # 输出到文件
        """
    )

    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="快速模式，跳过网络相关测试"
    )

    parser.add_argument(
        "--news",
        type=str,
        metavar="SYMBOL",
        help="测试新闻获取功能（指定股票代码）"
    )

    parser.add_argument(
        "--stock",
        type=str,
        metavar="SYMBOL",
        help="测试股票数据获取功能（指定股票代码）"
    )

    parser.add_argument(
        "--fifo",
        action="store_true",
        help="仅运行 FIFO 配对分析"
    )

    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="数据库路径（默认使用配置）"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出报告到 JSON 文件"
    )

    args = parser.parse_args()

    # 创建检查器
    checker = DataQualityChecker(db_path=args.db)

    # 根据参数执行检查
    if args.news:
        result = checker.check_news_fetcher(args.news)
        results = {"checks": {"news": result}}
    elif args.stock:
        result = checker.check_stock_data_fetcher(args.stock)
        results = {"checks": {"stock": result}}
    elif args.fifo:
        result = checker.check_fifo_matching()
        results = {"checks": {"fifo": result}}
    else:
        results = checker.run_all_checks(quick=args.quick)

    # 输出到文件
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"报告已保存到: {output_path}")

    # 返回退出码
    if results.get("overall_status") == "FAILED":
        sys.exit(1)
    elif results.get("overall_status") == "WARNING":
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
