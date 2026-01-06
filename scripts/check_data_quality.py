#!/usr/bin/env python3
"""
Data Quality Check Script - 数据质量检查脚本

input: SQLite database path
output: Data quality report (JSON/Terminal)
pos: 运维工具 - 定期检查数据质量

Usage:
    python scripts/check_data_quality.py                    # 检查并输出报告
    python scripts/check_data_quality.py --fix              # 检查并自动修复 (dry run)
    python scripts/check_data_quality.py --fix --apply      # 检查并应用修复
    python scripts/check_data_quality.py --json             # 输出 JSON 格式
    python scripts/check_data_quality.py --trace 123        # 追踪持仓 #123 的血缘

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
import os
import argparse
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validators.data_quality_monitor import DataQualityMonitor, run_quality_check
from src.validators.data_fixer import DataFixer, run_auto_fix
from src.validators.data_lineage import DataLineageTracker


def print_colored(text: str, color: str = "white"):
    """打印彩色文本"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")


def print_quality_report(dashboard: dict):
    """打印质量报告"""
    summary = dashboard["summary"]

    # 标题
    print("\n" + "=" * 60)
    print_colored("  📊 TradingCoach 数据质量报告", "cyan")
    print("=" * 60)
    print(f"生成时间: {dashboard['timestamp']}")

    # 健康状态
    health_colors = {
        "HEALTHY": "green",
        "GOOD": "blue",
        "WARNING": "yellow",
        "CRITICAL": "red",
    }
    status_color = health_colors.get(summary["health_status"], "white")
    print_colored(f"\n整体健康状态: {summary['health_status']} ({summary['overall_score']:.1f}分)", status_color)

    # 记录统计
    print(f"\n📈 数据统计")
    print(f"  总记录数: {summary['total_records']:,}")
    print(f"  异常数量: {summary['total_anomalies']}")
    print_colored(f"  严重问题: {summary['critical_issues']}", "red" if summary['critical_issues'] > 0 else "green")
    print_colored(f"  高危问题: {summary['high_issues']}", "yellow" if summary['high_issues'] > 0 else "green")

    # 表级质量
    print(f"\n📋 表级质量指标")
    for table_name, table_data in dashboard["tables"].items():
        level_colors = {
            "excellent": "green",
            "good": "blue",
            "fair": "yellow",
            "poor": "red",
            "critical": "red",
        }
        color = level_colors.get(table_data["quality_level"], "white")
        print(f"\n  [{table_name.upper()}] - {table_data['quality_level'].upper()}")
        print(f"    记录数: {table_data['total_records']:,}")
        print(f"    综合评分: {table_data['overall_score']:.1f}")
        print(f"    完整性: {table_data['completeness']:.1f}%")
        print(f"    准确性: {table_data['accuracy']:.1f}%")
        print(f"    一致性: {table_data['consistency']:.1f}%")
        if table_data.get('duplicates', 0) > 0:
            print_colored(f"    重复记录: {table_data['duplicates']}", "yellow")
        if table_data.get('outliers', 0) > 0:
            print_colored(f"    异常值: {table_data['outliers']}", "yellow")

    # 异常详情
    anomalies = dashboard["anomalies"]
    if anomalies["total"] > 0:
        print(f"\n⚠️ 异常详情 (共 {anomalies['total']} 个)")
        print(f"  按严重程度:")
        print(f"    严重: {anomalies['by_severity']['critical']}")
        print(f"    高危: {anomalies['by_severity']['high']}")
        print(f"    中等: {anomalies['by_severity']['medium']}")
        print(f"    低危: {anomalies['by_severity']['low']}")

        if anomalies["auto_fixable"] > 0:
            print_colored(f"\n  🔧 可自动修复: {anomalies['auto_fixable']} 个", "cyan")

        # 显示前 10 个异常
        print(f"\n  最近异常:")
        for i, anomaly in enumerate(anomalies["details"][:10], 1):
            severity_colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "cyan",
                "low": "white",
            }
            color = severity_colors.get(anomaly["severity"], "white")
            print_colored(f"    {i}. [{anomaly['severity'].upper()}] {anomaly['description']}", color)

    # 建议
    recommendations = dashboard.get("recommendations", [])
    if recommendations:
        print(f"\n💡 建议")
        for rec in recommendations:
            print(f"  {rec}")

    print("\n" + "=" * 60)


def print_fix_report(results: dict):
    """打印修复报告"""
    print("\n" + "=" * 60)
    print_colored("  🔧 数据质量自动修复报告", "cyan")
    print("=" * 60)
    print(f"执行时间: {results['timestamp']}")
    print_colored(f"模式: {'预览 (Dry Run)' if results['dry_run'] else '已应用'}",
                  "yellow" if results['dry_run'] else "green")

    print(f"\n修复结果:")
    for fix in results["fixes"]:
        status = "✓" if fix.get("success") else "✗"
        color = "green" if fix.get("success") else "red"
        print_colored(f"  {status} {fix['name']}", color)
        if fix.get("affected_count", 0) > 0:
            print(f"      影响记录: {fix['affected_count']}")
        if fix.get("message"):
            print(f"      {fix['message']}")
        if fix.get("error"):
            print_colored(f"      错误: {fix['error']}", "red")

    print(f"\n总计影响: {results['total_affected']} 条记录")

    if results['dry_run']:
        print_colored("\n提示: 使用 --apply 参数来实际应用修复", "yellow")

    print("=" * 60)


def print_lineage_report(lineage: dict):
    """打印血缘报告"""
    print("\n" + "=" * 60)
    print_colored("  🔗 数据血缘追踪", "cyan")
    print("=" * 60)

    if "error" in lineage:
        print_colored(f"错误: {lineage['error']}", "red")
        return

    print(f"表: {lineage['table']}")
    print(f"记录 ID: {lineage['record_id']}")
    print(f"来源文件: {lineage.get('source_file', 'N/A')}")
    print(f"来源行号: {lineage.get('source_row', 'N/A')}")
    print(f"导入批次: {lineage.get('import_batch', 'N/A')}")

    history = lineage.get("transformation_history", [])
    if history:
        print(f"\n转换历史:")
        for event in history:
            print(f"  [{event['timestamp']}] {event['type']}")
            print(f"    {event['description']}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="数据质量检查工具")
    parser.add_argument("--db", default="data/tradingcoach.db", help="数据库路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--fix", action="store_true", help="运行自动修复")
    parser.add_argument("--apply", action="store_true", help="应用修复 (默认 dry run)")
    parser.add_argument("--trace", type=int, help="追踪指定持仓的血缘")
    parser.add_argument("--history", action="store_true", help="显示导入历史")

    args = parser.parse_args()

    # 检查数据库是否存在
    if not os.path.exists(args.db):
        print_colored(f"错误: 数据库不存在: {args.db}", "red")
        sys.exit(1)

    # 追踪血缘
    if args.trace:
        tracker = DataLineageTracker(args.db)
        lineage = tracker.trace_record("positions", args.trace)
        if args.json:
            print(json.dumps(lineage, indent=2, ensure_ascii=False))
        else:
            print_lineage_report(lineage)
        return

    # 显示导入历史
    if args.history:
        tracker = DataLineageTracker(args.db)
        history = tracker.get_import_history()
        if args.json:
            print(json.dumps(history, indent=2, ensure_ascii=False))
        else:
            print("\n导入历史:")
            for h in history:
                print(f"  [{h['timestamp']}] {h['file_path']}")
                print(f"    记录数: {h['total_records']}, 批次: {h['event_id']}")
        return

    # 运行质量检查
    dashboard = run_quality_check(args.db)

    if args.json:
        print(json.dumps(dashboard, indent=2, ensure_ascii=False))
    else:
        print_quality_report(dashboard)

    # 运行修复
    if args.fix:
        dry_run = not args.apply
        results = run_auto_fix(args.db, dry_run=dry_run)

        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print_fix_report(results)

    # 返回状态码
    if dashboard["summary"]["critical_issues"] > 0:
        sys.exit(2)  # 有严重问题
    elif dashboard["summary"]["high_issues"] > 0:
        sys.exit(1)  # 有高危问题
    else:
        sys.exit(0)  # 正常


if __name__ == "__main__":
    main()
