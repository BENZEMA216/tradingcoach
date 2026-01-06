"""
数据库迁移：添加 news_context 表和相关字段

input: 现有数据库 (data/tradingcoach.db)
output: 添加 news_context 表，positions 表新增 news_alignment_score, news_context_id 字段
pos: 数据库迁移脚本 - 为新闻搜索功能准备数据结构

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from sqlalchemy import text
from src.models.base import init_database, get_session


def migrate():
    """执行数据库迁移"""
    print("=" * 60)
    print("数据库迁移: 添加 news_context 表和相关字段")
    print("=" * 60)

    # 初始化数据库连接
    engine = init_database(config.DATABASE_URL, echo=False)
    session = get_session()

    try:
        # 1. 创建 news_context 表
        print("\n[1/3] 创建 news_context 表...")

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS news_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- 关联信息
            position_id INTEGER NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            underlying_symbol VARCHAR(50),
            search_date DATE NOT NULL,
            search_range_days INTEGER DEFAULT 3,
            search_source VARCHAR(50) DEFAULT 'web_search',

            -- 新闻类别标记
            has_earnings BOOLEAN DEFAULT 0,
            has_product_news BOOLEAN DEFAULT 0,
            has_analyst_rating BOOLEAN DEFAULT 0,
            has_sector_news BOOLEAN DEFAULT 0,
            has_macro_news BOOLEAN DEFAULT 0,
            has_geopolitical BOOLEAN DEFAULT 0,

            -- 情感分析
            overall_sentiment VARCHAR(20),
            sentiment_score DECIMAL(6, 2),
            news_impact_level VARCHAR(20) DEFAULT 'none',

            -- 新闻数据存储
            news_items JSON,
            search_queries JSON,
            news_count INTEGER DEFAULT 0,

            -- 评分结果
            news_alignment_score DECIMAL(5, 2),
            score_breakdown JSON,
            scoring_warnings JSON,

            -- 缓存管理
            cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            cache_valid_until DATETIME,
            is_stale BOOLEAN DEFAULT 0,

            -- 时间戳
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            -- 外键约束
            FOREIGN KEY (position_id) REFERENCES positions(id)
        )
        """
        session.execute(text(create_table_sql))
        print("   news_context 表创建成功")

        # 2. 创建索引
        print("\n[2/3] 创建索引...")

        index_sqls = [
            "CREATE INDEX IF NOT EXISTS ix_news_context_position_id ON news_context(position_id)",
            "CREATE INDEX IF NOT EXISTS ix_news_context_symbol ON news_context(symbol)",
            "CREATE INDEX IF NOT EXISTS ix_news_context_search_date ON news_context(search_date)",
            "CREATE INDEX IF NOT EXISTS ix_news_context_symbol_date ON news_context(symbol, search_date)",
            "CREATE INDEX IF NOT EXISTS ix_news_context_cache ON news_context(symbol, search_date, is_stale)",
        ]

        for idx_sql in index_sqls:
            try:
                session.execute(text(idx_sql))
                idx_name = idx_sql.split("IF NOT EXISTS ")[1].split(" ON")[0]
                print(f"   索引 {idx_name} 创建成功")
            except Exception as e:
                print(f"   索引创建跳过: {e}")

        # 3. 检查并添加 positions 表字段
        print("\n[3/3] 更新 positions 表...")

        # 检查现有列
        result = session.execute(text("PRAGMA table_info(positions)"))
        existing_columns = {row[1] for row in result.fetchall()}

        # 添加 news_alignment_score 字段
        if 'news_alignment_score' not in existing_columns:
            session.execute(text(
                "ALTER TABLE positions ADD COLUMN news_alignment_score DECIMAL(5, 2)"
            ))
            print("   添加字段: news_alignment_score")
        else:
            print("   字段已存在: news_alignment_score")

        # 添加 news_context_id 字段
        if 'news_context_id' not in existing_columns:
            session.execute(text(
                "ALTER TABLE positions ADD COLUMN news_context_id INTEGER REFERENCES news_context(id)"
            ))
            print("   添加字段: news_context_id")
        else:
            print("   字段已存在: news_context_id")

        # 提交事务
        session.commit()

        print("\n" + "=" * 60)
        print("迁移完成!")
        print("=" * 60)

        # 验证
        print("\n验证迁移结果:")

        # 验证 news_context 表
        result = session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='news_context'"
        ))
        if result.fetchone():
            print("   [OK] news_context 表已创建")
        else:
            print("   [ERROR] news_context 表创建失败")

        # 验证 positions 新字段
        result = session.execute(text("PRAGMA table_info(positions)"))
        columns = {row[1] for row in result.fetchall()}

        if 'news_alignment_score' in columns:
            print("   [OK] positions.news_alignment_score 字段已添加")
        else:
            print("   [ERROR] positions.news_alignment_score 字段添加失败")

        if 'news_context_id' in columns:
            print("   [OK] positions.news_context_id 字段已添加")
        else:
            print("   [ERROR] positions.news_context_id 字段添加失败")

    except Exception as e:
        print(f"\n[ERROR] 迁移失败: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate()
