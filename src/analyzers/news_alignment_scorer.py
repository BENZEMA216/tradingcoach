"""
NewsAlignmentScorer - 新闻契合度评分器

input: NewsSearchResult, Position (方向、开仓时间)
output: 新闻契合度评分 (0-100)，评分细节
pos: 分析器层 - 评估交易决策与新闻背景的契合程度

评分维度:
- 方向对齐 (40%): 交易方向是否与新闻情绪一致
- 时机质量 (30%): 是否在新闻发布前/后合理时机入场
- 信息完整度 (20%): 是否有足够的新闻背景做决策
- 风险意识 (10%): 是否避开高风险事件（财报、地缘政治）

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import logging
from datetime import date
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .news_searcher import NewsSearchResult

logger = logging.getLogger(__name__)


@dataclass
class NewsAlignmentScore:
    """新闻契合度评分结果"""
    # 总分
    overall_score: float = 50.0  # 0-100

    # 分项评分
    direction_score: float = 50.0  # 方向对齐 (0-100)
    timing_score: float = 50.0     # 时机质量 (0-100)
    completeness_score: float = 50.0  # 信息完整度 (0-100)
    risk_awareness_score: float = 50.0  # 风险意识 (0-100)

    # 评分细节
    breakdown: Dict[str, Any] = field(default_factory=dict)

    # 警告信息
    warnings: List[str] = field(default_factory=list)

    # 元数据
    news_count: int = 0
    news_sentiment: str = "neutral"
    news_impact: str = "none"


class NewsAlignmentScorer:
    """
    新闻契合度评分器

    评估交易决策与新闻背景的契合程度。
    """

    # 权重配置
    WEIGHT_DIRECTION = 0.40    # 方向对齐
    WEIGHT_TIMING = 0.30       # 时机质量
    WEIGHT_COMPLETENESS = 0.20 # 信息完整度
    WEIGHT_RISK = 0.10         # 风险意识

    def __init__(self):
        """初始化评分器"""
        pass

    def score(
        self,
        news_result: NewsSearchResult,
        position_direction: str,  # 'long' or 'short'
        position_open_date: date,
    ) -> NewsAlignmentScore:
        """
        计算新闻契合度评分

        Args:
            news_result: 新闻搜索结果
            position_direction: 持仓方向 ('long' 或 'short')
            position_open_date: 开仓日期

        Returns:
            NewsAlignmentScore: 评分结果
        """
        result = NewsAlignmentScore(
            news_count=news_result.news_count,
            news_sentiment=news_result.overall_sentiment,
            news_impact=news_result.news_impact_level,
        )

        # 1. 方向对齐评分
        result.direction_score = self._score_direction_alignment(
            news_result, position_direction
        )

        # 2. 时机质量评分
        result.timing_score = self._score_timing_quality(
            news_result, position_open_date
        )

        # 3. 信息完整度评分
        result.completeness_score = self._score_completeness(news_result)

        # 4. 风险意识评分
        result.risk_awareness_score = self._score_risk_awareness(
            news_result, position_direction
        )

        # 计算加权总分
        result.overall_score = (
            result.direction_score * self.WEIGHT_DIRECTION +
            result.timing_score * self.WEIGHT_TIMING +
            result.completeness_score * self.WEIGHT_COMPLETENESS +
            result.risk_awareness_score * self.WEIGHT_RISK
        )

        # 生成评分细节
        result.breakdown = {
            'direction': {
                'score': result.direction_score,
                'weight': self.WEIGHT_DIRECTION,
                'position_direction': position_direction,
                'news_sentiment': news_result.overall_sentiment,
                'sentiment_score': news_result.sentiment_score,
            },
            'timing': {
                'score': result.timing_score,
                'weight': self.WEIGHT_TIMING,
                'open_date': str(position_open_date),
                'search_date': str(news_result.search_date),
            },
            'completeness': {
                'score': result.completeness_score,
                'weight': self.WEIGHT_COMPLETENESS,
                'news_count': news_result.news_count,
                'categories_covered': self._count_categories(news_result),
            },
            'risk_awareness': {
                'score': result.risk_awareness_score,
                'weight': self.WEIGHT_RISK,
                'has_high_risk_events': (
                    news_result.has_earnings or news_result.has_geopolitical
                ),
                'news_impact': news_result.news_impact_level,
            },
        }

        # 生成警告
        result.warnings = self._generate_warnings(news_result, position_direction)

        logger.debug(
            f"News alignment score: {result.overall_score:.1f} "
            f"(dir={result.direction_score:.0f}, time={result.timing_score:.0f}, "
            f"comp={result.completeness_score:.0f}, risk={result.risk_awareness_score:.0f})"
        )

        return result

    def _score_direction_alignment(
        self,
        news_result: NewsSearchResult,
        position_direction: str
    ) -> float:
        """
        评估交易方向与新闻情绪的对齐程度

        - 做多 + 看涨新闻 = 高分
        - 做空 + 看跌新闻 = 高分
        - 做多 + 看跌新闻 = 低分 (逆势)
        - 做空 + 看涨新闻 = 低分 (逆势)
        - 中性/无新闻 = 中等分数
        """
        sentiment = news_result.overall_sentiment
        sentiment_score = news_result.sentiment_score  # -100 to +100

        # 无新闻时给中等分数
        if news_result.news_count == 0 or sentiment == "neutral":
            return 60.0

        is_long = position_direction.lower() == 'long'
        is_bullish = sentiment == "bullish"
        is_bearish = sentiment == "bearish"
        is_mixed = sentiment == "mixed"

        if is_long:
            if is_bullish:
                # 完美对齐: 做多 + 看涨
                # 情感分数越高，评分越高
                base_score = 85
                bonus = min(15, abs(sentiment_score) / 100 * 15)
                return base_score + bonus
            elif is_bearish:
                # 逆势操作: 做多 + 看跌
                # 需要勇气，但风险高，给较低分
                base_score = 30
                # 如果情感很强烈的看跌，分数更低
                penalty = min(20, abs(sentiment_score) / 100 * 20)
                return max(10, base_score - penalty)
            else:  # mixed
                return 55.0
        else:  # short
            if is_bearish:
                # 完美对齐: 做空 + 看跌
                base_score = 85
                bonus = min(15, abs(sentiment_score) / 100 * 15)
                return base_score + bonus
            elif is_bullish:
                # 逆势操作: 做空 + 看涨
                base_score = 30
                penalty = min(20, abs(sentiment_score) / 100 * 20)
                return max(10, base_score - penalty)
            else:  # mixed
                return 55.0

    def _score_timing_quality(
        self,
        news_result: NewsSearchResult,
        position_open_date: date
    ) -> float:
        """
        评估入场时机与新闻发布的关系

        - 在重大新闻前入场（提前布局）= 高分
        - 在重大新闻后合理时间入场 = 中高分
        - 无明显新闻时机 = 中等分
        """
        if news_result.news_count == 0:
            return 50.0  # 无新闻参考时给中等分

        # 统计新闻日期分布
        before_count = 0  # 开仓日之前的新闻
        on_date_count = 0  # 开仓日当天的新闻
        after_count = 0   # 开仓日之后的新闻

        for item in news_result.news_items:
            if item.date:
                if item.date < position_open_date:
                    before_count += 1
                elif item.date == position_open_date:
                    on_date_count += 1
                else:
                    after_count += 1

        total = before_count + on_date_count + after_count
        if total == 0:
            return 50.0

        # 评分逻辑
        score = 50.0

        # 有新闻在开仓日之前（说明是基于已知信息决策）
        if before_count > 0:
            score += 15 * min(1.0, before_count / 3)

        # 开仓日当天有新闻（可能是追新闻）
        if on_date_count > 0:
            if news_result.news_impact_level == "high":
                # 高影响新闻当天入场，可能是追涨杀跌
                score -= 5
            else:
                score += 10

        # 大部分新闻在开仓后（说明是提前布局）
        if after_count > before_count and news_result.news_impact_level == "high":
            score += 20  # 成功预判重大新闻

        return min(100, max(0, score))

    def _score_completeness(self, news_result: NewsSearchResult) -> float:
        """
        评估新闻信息的完整度

        - 覆盖多个类别（个股、行业、宏观）= 高分
        - 新闻数量充足 = 高分
        - 信息匮乏 = 低分
        """
        score = 30.0  # 基础分

        # 新闻数量
        if news_result.news_count >= 5:
            score += 25
        elif news_result.news_count >= 3:
            score += 15
        elif news_result.news_count >= 1:
            score += 5

        # 类别覆盖度
        categories = self._count_categories(news_result)
        if categories >= 4:
            score += 30
        elif categories >= 3:
            score += 20
        elif categories >= 2:
            score += 10
        elif categories >= 1:
            score += 5

        # 特别加分: 有关键类别
        if news_result.has_earnings:
            score += 5  # 财报是重要参考
        if news_result.has_analyst_rating:
            score += 5  # 分析师评级是重要参考

        return min(100, score)

    def _count_categories(self, news_result: NewsSearchResult) -> int:
        """统计覆盖的新闻类别数量"""
        count = 0
        if news_result.has_earnings:
            count += 1
        if news_result.has_product_news:
            count += 1
        if news_result.has_analyst_rating:
            count += 1
        if news_result.has_sector_news:
            count += 1
        if news_result.has_macro_news:
            count += 1
        if news_result.has_geopolitical:
            count += 1
        return count

    def _score_risk_awareness(
        self,
        news_result: NewsSearchResult,
        position_direction: str
    ) -> float:
        """
        评估风险意识

        - 在高风险事件（财报、地缘政治）期间交易 = 需要谨慎评估
        - 避开高风险事件 = 高分
        - 在高风险事件中正确判断方向 = 中高分
        """
        has_high_risk = news_result.has_earnings or news_result.has_geopolitical

        if not has_high_risk:
            # 无高风险事件，给予较高分
            return 80.0

        # 有高风险事件时，评估方向判断是否正确
        is_long = position_direction.lower() == 'long'
        sentiment = news_result.overall_sentiment

        if is_long and sentiment == "bullish":
            # 在高风险事件中做多且看涨，方向正确
            return 70.0
        elif not is_long and sentiment == "bearish":
            # 在高风险事件中做空且看跌，方向正确
            return 70.0
        elif sentiment == "neutral" or sentiment == "mixed":
            # 方向不明确时交易，风险较高
            return 45.0
        else:
            # 方向判断错误
            return 30.0

    def _generate_warnings(
        self,
        news_result: NewsSearchResult,
        position_direction: str
    ) -> List[str]:
        """生成警告信息"""
        warnings = []

        # 逆势警告
        is_long = position_direction.lower() == 'long'
        sentiment = news_result.overall_sentiment

        if is_long and sentiment == "bearish":
            warnings.append("逆势做多：新闻情绪偏空，但持仓做多")
        elif not is_long and sentiment == "bullish":
            warnings.append("逆势做空：新闻情绪偏多，但持仓做空")

        # 高风险事件警告
        if news_result.has_earnings:
            warnings.append("财报期间交易：注意财报发布可能带来的剧烈波动")
        if news_result.has_geopolitical:
            warnings.append("地缘政治风险：存在地缘政治相关新闻，波动风险较高")

        # 信息不足警告
        if news_result.news_count == 0:
            warnings.append("信息不足：未找到相关新闻，建议额外研究")
        elif news_result.news_count < 3:
            warnings.append("信息有限：相关新闻较少，决策依据可能不充分")

        # 高影响事件警告
        if news_result.news_impact_level == "high":
            warnings.append("高影响事件：存在重大新闻事件，市场波动可能加剧")

        return warnings

    def to_dict(self, score: NewsAlignmentScore) -> Dict[str, Any]:
        """将评分结果转换为字典"""
        return {
            'overall_score': score.overall_score,
            'direction_score': score.direction_score,
            'timing_score': score.timing_score,
            'completeness_score': score.completeness_score,
            'risk_awareness_score': score.risk_awareness_score,
            'breakdown': score.breakdown,
            'warnings': score.warnings,
            'news_count': score.news_count,
            'news_sentiment': score.news_sentiment,
            'news_impact': score.news_impact,
        }
