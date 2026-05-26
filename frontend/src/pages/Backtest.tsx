/**
 * Counterfactual backtest page.
 *
 * Shows "if you'd done X back then, would the cumulative P&L have been higher?"
 * for 5 mechanical behavioral rules. Each rule has:
 *   - a summary card with savings vs actual
 *   - expandable: a dual-line cumulative P&L chart (actual vs counterfactual)
 *     + a list of symbols most affected.
 *
 * Backend: GET /api/v1/backtest/summary (all rules, sorted by savings)
 *          GET /api/v1/backtest/run/{rule_id}?params (parameter tuning, not used in v1)
 */

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';
import { StableResponsiveContainer as ResponsiveContainer } from '@/components/charts/StableResponsiveContainer';
import { backtestApi, type BacktestResult } from '@/api/client';
import { formatCurrency } from '@/utils/format';

function formatSavingsPct(value: BacktestResult['savings_pct'], isZh: boolean) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return isZh ? '百分比不稳定' : 'unstable %';
  }
  return `${value >= 0 ? '+' : ''}${value.toFixed(0)}%`;
}

function formatBacktestDeltaLabel(result: BacktestResult, isZh: boolean) {
  if (result.savings > 0) {
    return isZh ? '模拟改善' : 'simulated improvement';
  }

  if (result.savings < 0) {
    return isZh ? '模拟变差' : 'simulated drag';
  }

  return isZh ? '模拟持平' : 'simulated flat';
}

function formatBacktestDeltaRatio(result: BacktestResult, isZh: boolean) {
  if (typeof result.savings_pct !== 'number' || !Number.isFinite(result.savings_pct)) {
    return isZh ? '实际盈亏接近 0，比例不稳定' : 'unstable: actual P&L near 0';
  }

  return isZh
    ? `${formatSavingsPct(result.savings_pct, isZh)} / |实际盈亏| ${formatCurrency(Math.abs(result.actual_total_pnl))}`
    : `${formatSavingsPct(result.savings_pct, isZh)} / |actual P&L| ${formatCurrency(Math.abs(result.actual_total_pnl))}`;
}

function buildBacktestSummary(results: BacktestResult[], isZh: boolean) {
  if (results.length === 0) return null;

  const positiveRules = results.filter((rule) => rule.savings > 0);
  const negativeRules = results.filter((rule) => rule.savings < 0);
  const bestRule = positiveRules[0];
  const secondRule = positiveRules[1];
  const worstRule = [...results].sort((a, b) => a.savings - b.savings)[0];

  if (!bestRule) {
    return {
      tone: 'negative' as const,
      title: isZh ? '当前规则没有改善历史结果' : 'These rules did not improve the historical result',
      body: isZh
        ? '这组机械规则在历史数据上没有带来正收益，说明它们不适合直接套用。更合理的下一步是缩小条件或重新设计规则，再做参数测试。'
        : 'None of these mechanical rules improved the historical result. They should not be applied directly; narrow the conditions or redesign the rules before parameter testing.',
      callout: isZh ? '先不要把这些规则当作交易纪律。' : 'Do not treat these as trading rules yet.',
    };
  }

  const bestName = isZh ? bestRule.name_cn : bestRule.name_en;
  const secondName = secondRule ? (isZh ? secondRule.name_cn : secondRule.name_en) : null;
  const worstName = worstRule && worstRule.savings < 0 ? (isZh ? worstRule.name_cn : worstRule.name_en) : null;

  return {
    tone: 'positive' as const,
    title: isZh ? '核心结论：优先处理大亏和长期亏损标的' : 'Key takeaway: cap large losses and avoid persistent losers first',
    body: isZh
      ? `${bestName} 是历史模拟里最有效的规则，少做/更早处理 ${bestRule.skipped_count} 笔交易，理论上可改善 ${formatCurrency(bestRule.savings)}。${secondName ? `${secondName} 也有效，说明亏损主要集中在少数持续拖累的标的。` : ''}`
      : `${bestName} was the strongest historical rule: changing ${bestRule.skipped_count} trades would have improved the result by ${formatCurrency(bestRule.savings)}. ${secondName ? `${secondName} also helped, suggesting losses were concentrated in a few persistent-loser symbols.` : ''}`,
    callout: isZh
      ? `${worstName ? `${worstName} 在当前参数下反而变差，` : ''}所以这页不是让你一次启用所有规则，而是提示优先测试“硬止损”和“亏损标的过滤”，再单独调参验证。`
      : `${worstName ? `${worstName} got worse with the current parameters, ` : ''}so this page is not telling you to enable every rule. Prioritize hard stops and persistent-loser filters, then tune each rule separately.`,
    positiveCount: positiveRules.length,
    negativeCount: negativeRules.length,
  };
}

export function Backtest() {
  const { i18n } = useTranslation();
  const isZh = i18n.language === 'zh';
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data: results, isLoading, error } = useQuery({
    queryKey: ['backtest', 'summary'],
    queryFn: backtestApi.summary,
  });

  if (isLoading) {
    return (
      <div className="p-6 text-white/60 font-mono">
        {isZh ? '回测中...' : 'Running backtest...'}
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="p-6 text-red-500 font-mono">
        {isZh ? '回测失败：' : 'Backtest failed: '}
        {(error as Error)?.message || 'no data'}
      </div>
    );
  }

  const summary = buildBacktestSummary(results, isZh);

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-slate-900 dark:text-white tracking-tight uppercase">
          {isZh ? '回测分析' : 'COUNTERFACTUAL BACKTEST'}
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-white/50 font-mono">
          {isZh
            ? '如果当时按这些规则交易，累计盈亏会怎样？'
            : 'What if you had followed these rules at the time? Cumulative-P&L counterfactuals.'}
        </p>
      </div>

      {summary && (
        <div
          className={clsx(
            'rounded-sm border px-6 py-5',
            summary.tone === 'positive'
              ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-500/20'
              : 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-500/20'
          )}
        >
          <div className="flex items-start justify-between gap-6">
            <div className="min-w-0">
              <div
                className={clsx(
                  'text-[10px] font-mono uppercase tracking-widest',
                  summary.tone === 'positive'
                    ? 'text-emerald-700 dark:text-emerald-400'
                    : 'text-amber-700 dark:text-amber-400'
                )}
              >
                {isZh ? '整体解读' : 'Summary'}
              </div>
              <h2 className="mt-2 text-base font-mono font-bold text-slate-900 dark:text-white">
                {summary.title}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-white/60">
                {summary.body}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-white/70">
                {summary.callout}
              </p>
            </div>
            {'positiveCount' in summary && (
              <div className="hidden sm:grid grid-cols-2 gap-3 shrink-0 text-center font-mono">
                <div className="rounded-sm bg-white/70 dark:bg-black/30 border border-emerald-200/70 dark:border-emerald-500/20 px-4 py-3">
                  <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                    {summary.positiveCount}
                  </div>
                  <div className="mt-1 text-[10px] uppercase tracking-widest text-slate-400">
                    {isZh ? '有效规则' : 'helped'}
                  </div>
                </div>
                <div className="rounded-sm bg-white/70 dark:bg-black/30 border border-red-200/70 dark:border-red-500/20 px-4 py-3">
                  <div className="text-xl font-bold text-red-600 dark:text-red-400">
                    {summary.negativeCount}
                  </div>
                  <div className="mt-1 text-[10px] uppercase tracking-widest text-slate-400">
                    {isZh ? '需调参' : 'needs tuning'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Rule cards, sorted by savings desc */}
      <div className="space-y-4">
        {results.length === 0 ? (
          <div className="bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 px-6 py-10 text-center text-sm text-slate-500 dark:text-white/40 font-mono">
            {isZh ? '暂无可回测规则' : 'No backtest rules available'}
          </div>
        ) : results.map((r, idx) => {
          const isExpanded = expanded === r.rule_id;
          const positive = r.savings > 0;
          return (
            <div
              key={r.rule_id}
              className="bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 overflow-hidden transition-colors"
            >
              {/* Card header */}
              <button
                onClick={() => setExpanded(isExpanded ? null : r.rule_id)}
                className="w-full flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 px-6 py-4 hover:bg-neutral-50 dark:hover:bg-white/5 transition-colors text-left"
              >
                <div className="flex items-center gap-4 min-w-0 w-full sm:w-auto sm:flex-1">
                  <div className="flex items-center justify-center w-8 h-8 rounded-sm bg-neutral-100 dark:bg-white/10 text-xs font-mono font-bold text-slate-700 dark:text-white/80">
                    {idx + 1}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-baseline gap-2">
                      <h3 className="text-base font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                        {isZh ? r.name_cn : r.name_en}
                      </h3>
                      <span className="text-xs font-mono text-slate-400 dark:text-white/40">
                        {isZh ? `跳过 ${r.skipped_count} 笔` : `${r.skipped_count} skipped`}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500 dark:text-white/50 font-mono truncate">
                      {r.notes}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-6 shrink-0 self-end sm:self-auto">
                  <div className="text-right">
                    <div
                      className={clsx(
                        'text-2xl font-mono font-bold tracking-tight',
                        positive ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                      )}
                    >
                      {positive ? '+' : ''}
                      {formatCurrency(r.savings)}
                    </div>
                    <div className="text-[10px] font-mono uppercase tracking-widest text-slate-400 dark:text-white/40 mt-1">
                      {formatBacktestDeltaLabel(r, isZh)}
                    </div>
                    <div className="text-xs font-mono text-slate-500 dark:text-white/50 mt-0.5 leading-tight">
                      {formatBacktestDeltaRatio(r, isZh)}
                    </div>
                  </div>
                </div>
              </button>

              {/* Expanded body */}
              {isExpanded && (
                <div className="border-t border-neutral-200 dark:border-white/10 px-6 py-5 space-y-5 bg-neutral-50 dark:bg-black/40">
                  {/* Totals row */}
                  <div className="grid grid-cols-3 gap-4 text-sm font-mono">
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-slate-400 dark:text-white/40">
                        {isZh ? '实际盈亏' : 'Actual'}
                      </div>
                      <div className="text-lg font-bold text-slate-900 dark:text-white mt-1">
                        {formatCurrency(r.actual_total_pnl)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-slate-400 dark:text-white/40">
                        {isZh ? '反事实盈亏' : 'Counterfactual'}
                      </div>
                      <div className="text-lg font-bold text-blue-600 dark:text-blue-400 mt-1">
                        {formatCurrency(r.counterfactual_total_pnl)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-slate-400 dark:text-white/40">
                        {isZh ? '影响标的数' : 'Symbols Affected'}
                      </div>
                      <div className="text-lg font-bold text-slate-900 dark:text-white mt-1">
                        {Object.keys(r.skipped_by_symbol).length}
                      </div>
                    </div>
                  </div>

                  {/* Cumulative chart */}
                  <div className="h-64 bg-white dark:bg-black/60 rounded-sm border border-neutral-200 dark:border-white/10 p-3">
                    <ResponsiveContainer width="100%" height="100%" minHeight={200}>
                      <LineChart
                        data={r.monthly}
                        margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(150,150,150,0.15)" />
                        <XAxis dataKey="month" stroke="#888" fontSize={10} />
                        <YAxis
                          stroke="#888"
                          fontSize={10}
                          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
                        />
                        <Tooltip
                          contentStyle={{ background: '#111', border: '1px solid #333', fontSize: 11 }}
                          formatter={(val: number) => formatCurrency(val)}
                        />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        <Line
                          type="monotone"
                          dataKey="actual_cumulative"
                          stroke="#94a3b8"
                          strokeWidth={2}
                          dot={false}
                          name={isZh ? '实际累计' : 'Actual cumulative'}
                        />
                        <Line
                          type="monotone"
                          dataKey="cf_cumulative"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={false}
                          name={isZh ? '反事实累计' : 'Counterfactual cumulative'}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Top affected symbols */}
                  {Object.keys(r.skipped_by_symbol).length > 0 && (
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-slate-400 dark:text-white/40 mb-2">
                        {isZh ? '影响最大的标的 (top 10)' : 'Top affected symbols (top 10)'}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(r.skipped_by_symbol)
                          .sort((a, b) => b[1] - a[1])
                          .slice(0, 10)
                          .map(([sym, count]) => (
                            <span
                              key={sym}
                              className="inline-flex items-center gap-1 px-2 py-1 rounded-sm bg-neutral-100 dark:bg-white/10 text-xs font-mono"
                            >
                              <span className="text-slate-700 dark:text-white">{sym}</span>
                              <span className="text-slate-400 dark:text-white/40">×{count}</span>
                            </span>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footnote */}
      <p className="text-xs text-slate-400 dark:text-white/30 font-mono leading-relaxed">
        {isZh
          ? '* 每条规则用"当时已知的信息"机械应用于历史交易，避免 look-ahead bias。改善金额 = 反事实盈亏 - 实际盈亏；百分比 = 改善金额 / |实际盈亏|。所有金额按近似汇率换算成 USD 等价。'
          : '* Each rule is applied mechanically to past trades using only info available at the time (no look-ahead bias). Improvement = counterfactual P&L - actual P&L; percentage = improvement / |actual P&L|. Amounts are USD-equivalent.'}
      </p>
    </div>
  );
}
