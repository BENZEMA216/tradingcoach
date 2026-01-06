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
            flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-all duration-200
            ${
              isPrivacyMode
                ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600'
            }
          `}
          aria-label={isZh ? '切换隐私模式' : 'Toggle privacy mode'}
        >
          {isPrivacyMode ? (
            <EyeOff className="w-4 h-4" />
          ) : (
            <Eye className="w-4 h-4" />
          )}
          <span className="hidden sm:inline font-medium">
            {isPrivacyMode
              ? isZh
                ? '隐私模式'
                : 'Privacy'
              : isZh
                ? '显示金额'
                : 'Show $'}
          </span>
          {isPrivacyMode && initialCapital && (
            <span className="hidden lg:inline text-xs opacity-70">
              ({formatCapitalDisplay(initialCapital)})
            </span>
          )}
        </button>
        {isPrivacyMode && initialCapital && (
          <button
            onClick={handleSettingsClick}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors text-gray-500 dark:text-gray-400"
            title={isZh ? '修改初始资本' : 'Change initial capital'}
          >
            <Settings className="w-4 h-4" />
          </button>
        )}
      </div>

      <InitialCapitalModal isOpen={showModal} onClose={() => setShowModal(false)} />
    </>
  );
}
