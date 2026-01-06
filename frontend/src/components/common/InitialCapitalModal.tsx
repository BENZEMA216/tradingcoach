/**
 * Initial Capital Modal
 * input: isOpen, onClose callback
 * output: Modal form for setting initial capital
 * pos: First-time setup for privacy mode
 *
 * Once updated, update this header
 */
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { X, DollarSign, Info, Percent } from 'lucide-react';
import { usePrivacyStore } from '@/store/usePrivacyStore';

interface InitialCapitalModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PRESET_AMOUNTS = [10000, 25000, 50000, 100000, 250000, 500000, 1000000];

export function InitialCapitalModal({ isOpen, onClose }: InitialCapitalModalProps) {
  const { i18n } = useTranslation();
  const isZh = i18n.language === 'zh';
  const { setInitialCapital, initialCapital, resetPrivacySettings } = usePrivacyStore();

  const [customAmount, setCustomAmount] = useState('');
  const [selectedPreset, setSelectedPreset] = useState<number | null>(null);

  // Initialize with current capital if editing
  useEffect(() => {
    if (isOpen && initialCapital) {
      if (PRESET_AMOUNTS.includes(initialCapital)) {
        setSelectedPreset(initialCapital);
        setCustomAmount('');
      } else {
        setSelectedPreset(null);
        setCustomAmount(initialCapital.toString());
      }
    }
  }, [isOpen, initialCapital]);

  if (!isOpen) return null;

  const handleSubmit = () => {
    const amount = selectedPreset || parseFloat(customAmount);
    if (amount && amount > 0) {
      setInitialCapital(amount);
      onClose();
    }
  };

  const handleReset = () => {
    resetPrivacySettings();
    setSelectedPreset(null);
    setCustomAmount('');
    onClose();
  };

  const formatPreset = (amount: number): string => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(0)}M`;
    }
    return `$${(amount / 1000).toFixed(0)}K`;
  };

  const currentAmount = selectedPreset || parseFloat(customAmount) || 0;
  const examplePnL = 1500;
  const examplePercent = currentAmount > 0 ? ((examplePnL / currentAmount) * 100).toFixed(2) : '?';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
              <Percent className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {isZh ? '设置初始资本' : 'Set Initial Capital'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {/* Explanation */}
          <div className="flex gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800">
            <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <p>
                {isZh
                  ? '开启隐私模式后，所有金额将显示为初始资本的百分比，方便分享截图。'
                  : 'When privacy mode is enabled, all amounts will be shown as a percentage of your initial capital, making it easier to share screenshots.'}
              </p>
              {currentAmount > 0 && (
                <p className="mt-2 font-medium">
                  {isZh ? '示例' : 'Example'}: $1,500 → {examplePercent}%
                </p>
              )}
            </div>
          </div>

          {/* Preset amounts */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              {isZh ? '选择预设金额' : 'Select preset amount'}
            </label>
            <div className="grid grid-cols-4 gap-2">
              {PRESET_AMOUNTS.map((amount) => (
                <button
                  key={amount}
                  onClick={() => {
                    setSelectedPreset(amount);
                    setCustomAmount('');
                  }}
                  className={`
                    py-2.5 text-sm font-medium rounded-lg border-2 transition-all duration-150
                    ${
                      selectedPreset === amount
                        ? 'bg-blue-600 text-white border-blue-600 shadow-md scale-105'
                        : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20'
                    }
                  `}
                >
                  {formatPreset(amount)}
                </button>
              ))}
            </div>
          </div>

          {/* Custom amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {isZh ? '或输入自定义金额' : 'Or enter custom amount'}
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="number"
                value={customAmount}
                onChange={(e) => {
                  setCustomAmount(e.target.value);
                  setSelectedPreset(null);
                }}
                placeholder={isZh ? '输入金额...' : 'Enter amount...'}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-900 transition-all"
                min="1"
                step="1000"
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          {initialCapital && (
            <button
              onClick={handleReset}
              className="px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            >
              {isZh ? '关闭隐私模式' : 'Disable Privacy'}
            </button>
          )}
          <div className="flex-1" />
          <button
            onClick={onClose}
            className="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            {isZh ? '取消' : 'Cancel'}
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedPreset && !customAmount}
            className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md hover:shadow-lg"
          >
            {isZh ? '确认并开启' : 'Confirm & Enable'}
          </button>
        </div>
      </div>
    </div>
  );
}
