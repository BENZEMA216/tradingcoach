/**
 * Privacy Mode Toggle Component
 * input: usePrivacyStore state
 * output: Toggle button with modal trigger
 * pos: Toolbar control for privacy mode feature
 *
 * Once updated, update this header
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { EyeOff, Eye, Settings } from 'lucide-react';
import { usePrivacyStore } from '@/store/usePrivacyStore';
import { InitialCapitalModal } from './InitialCapitalModal';

export function PrivacyModeToggle() {
  const { i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  const { isPrivacyMode, hasSetCapital, togglePrivacyMode, initialCapital } =
    usePrivacyStore();
  const [showModal, setShowModal] = useState(false);

  const handleToggle = () => {
    if (!hasSetCapital && !isPrivacyMode) {
      // First time enabling - show modal to set capital
      setShowModal(true);
    } else {
      togglePrivacyMode();
    }
  };

  const handleSettingsClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowModal(true);
  };

  const formatCapitalDisplay = (amount: number): string => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    }
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount}`;
  };

  return (
    <>
      <div
        className="flex items-center gap-1"
        title={isZh ? '隐私模式 - 将金额显示为资本百分比' : 'Privacy Mode - Show amounts as % of capital'}
      >
        <button
          onClick={handleToggle}
          className={`
            flex items-center gap-2 px-3 py-1.5 text-xs font-mono font-bold uppercase tracking-wider rounded-sm transition-all duration-200
            ${isPrivacyMode
              ? 'bg-white text-black border border-white'
              : 'bg-black text-white border border-white/10 hover:border-white/30'
            }
          `}
          aria-label={isZh ? '切换隐私模式' : 'Toggle privacy mode'}
        >
          {isPrivacyMode ? (
            <EyeOff className="w-3 h-3" />
          ) : (
            <Eye className="w-3 h-3 text-white/50" />
          )}
          <span className="hidden sm:inline">
            {isPrivacyMode
              ? isZh
                ? '隐私模式'
                : 'PRIVACY: ON'
              : isZh
                ? '显示金额'
                : 'PRIVACY: OFF'}
          </span>
          {isPrivacyMode && initialCapital && (
            <span className="hidden lg:inline text-[9px] opacity-70 ml-1">
              ({formatCapitalDisplay(initialCapital)})
            </span>
          )}
        </button>
        {isPrivacyMode && initialCapital && (
          <button
            onClick={handleSettingsClick}
            className="p-1.5 hover:bg-white/10 rounded-sm transition-colors text-white/50 hover:text-white"
            title={isZh ? '修改初始资本' : 'Change initial capital'}
          >
            <Settings className="w-3 h-3" />
          </button>
        )}
      </div>

      <InitialCapitalModal isOpen={showModal} onClose={() => setShowModal(false)} />
    </>
  );
}
