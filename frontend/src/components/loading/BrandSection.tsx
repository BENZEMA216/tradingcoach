/**
 * BrandSection - 品牌展示区域
 *
 * input: 任务状态
 * output: 品牌 slogan 和状态指示
 * pos: 组件 - Loading页面左侧品牌区
 */
import { TrendingUp, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface BrandSectionProps {
  status?: string;
}

export function BrandSection({ status }: BrandSectionProps) {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  const getStatusText = () => {
    switch (status) {
      case 'completed':
        return t('loading.statusComplete', 'ANALYSIS COMPLETE');
      case 'failed':
        return t('loading.statusFailed', 'ANALYSIS FAILED');
      case 'cancelled':
        return t('loading.statusCancelled', 'ANALYSIS CANCELLED');
      default:
        return t('loading.statusProcessing', 'SYSTEM PROCESSING');
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'text-green-500';
      case 'failed':
        return 'text-red-500';
      case 'cancelled':
        return 'text-yellow-500';
      default:
        return 'text-blue-500';
    }
  };

  const StatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
    }
  };

  return (
    <div className="text-center px-12">
      {/* Logo */}
      <div className="mb-12">
        <div className="w-16 h-16 bg-white text-black flex items-center justify-center rounded-sm mx-auto mb-6">
          <TrendingUp className="w-10 h-10" />
        </div>
        <span className="text-xs font-mono tracking-widest uppercase text-white/40">
          TC_TERMINAL
        </span>
      </div>

      {/* Slogan */}
      <h1 className="text-6xl font-bold text-white mb-6 tracking-tighter leading-[0.9]">
        {isZh ? (
          <>极致<br />阿尔法</>
        ) : (
          <>PURE<br />ALPHA.</>
        )}
      </h1>

      <p className="text-lg text-white/40 max-w-sm mx-auto leading-relaxed font-light tracking-wide mb-12">
        {isZh ? (
          <>机构级<span className="text-white/70">精准指标</span>与<span className="text-white/70">交易心理分析</span></>
        ) : (
          <>Institutional-grade <span className="text-white/70">precision metrics</span> and{' '}
          <span className="text-white/70">psychological profiling</span>.</>
        )}
      </p>

      {/* Divider */}
      <div className="w-24 h-px bg-white/20 mx-auto mb-12" />

      {/* Status */}
      <div className="space-y-4">
        <div className="flex items-center justify-center space-x-2">
          <StatusIcon />
          <span className={`text-xs font-mono tracking-widest uppercase ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>

        <p className="text-xs font-mono text-white/30 tracking-wider">
          v0.9.2 • {new Date().toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
