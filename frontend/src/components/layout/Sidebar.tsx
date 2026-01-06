import { NavLink, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  List,
  BarChart3,
  TrendingUp,
  Calendar,
  Upload,
  Home,
} from 'lucide-react';
import clsx from 'clsx';
import { LanguageSwitcher } from '@/components/common';

// Main navigation items (simplified)
const navItems = [
  { to: '/statistics', icon: BarChart3, labelKey: 'nav.statistics' },
  { to: '/positions', icon: List, labelKey: 'nav.positions' },
  { to: '/events', icon: Calendar, labelKey: 'nav.events' },
];

export function Sidebar() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-800 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-neutral-200 dark:border-neutral-800">
        <TrendingUp className="w-8 h-8 text-blue-600" />
        <span className="ml-3 text-xl font-bold text-neutral-900 dark:text-white">
          TradingCoach
        </span>
      </div>

      {/* Home Button */}
      <div className="px-3 pt-4">
        <button
          onClick={() => navigate('/')}
          className="w-full flex items-center px-4 py-2.5 rounded-lg text-sm font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
        >
          <Home className="w-4 h-4 mr-2" />
          {t('nav.home', '首页')}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3">
        <p className="px-4 mb-2 text-xs font-medium text-neutral-400 dark:text-neutral-500 uppercase tracking-wider">
          {t('nav.analysis', '分析')}
        </p>
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white'
                      : 'text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800'
                  )
                }
              >
                <item.icon className="w-5 h-5 mr-3" />
                {t(item.labelKey)}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Upload New Data */}
        <div className="mt-6 pt-4 border-t border-neutral-200 dark:border-neutral-800">
          <button
            onClick={() => navigate('/')}
            className="w-full flex items-center px-4 py-3 rounded-lg text-sm font-medium text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            <Upload className="w-5 h-5 mr-3" />
            {t('nav.uploadNew', '上传新数据')}
          </button>
        </div>
      </nav>

      {/* Footer with Language Switcher */}
      <div className="p-4 border-t border-neutral-200 dark:border-neutral-800 space-y-3">
        <div className="flex justify-center">
          <LanguageSwitcher />
        </div>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 text-center">
          TradingCoach v1.0
        </p>
      </div>
    </aside>
  );
}
