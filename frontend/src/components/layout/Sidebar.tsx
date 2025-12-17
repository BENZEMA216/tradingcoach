import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  List,
  BarChart3,
  Settings,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import clsx from 'clsx';
import { LanguageSwitcher } from '@/components/common';

const navItems = [
  { to: '/', icon: LayoutDashboard, labelKey: 'nav.dashboard' },
  { to: '/positions', icon: List, labelKey: 'nav.positions' },
  { to: '/statistics', icon: BarChart3, labelKey: 'nav.statistics' },
  { to: '/ai-coach', icon: Sparkles, labelKey: 'nav.aiCoach' },
  { to: '/system', icon: Settings, labelKey: 'nav.settings' },
];

export function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-700">
        <TrendingUp className="w-8 h-8 text-blue-600" />
        <span className="ml-3 text-xl font-bold text-gray-900 dark:text-white">
          Trading Coach
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3">
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
                      : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-neutral-800'
                  )
                }
              >
                <item.icon className="w-5 h-5 mr-3" />
                {t(item.labelKey)}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer with Language Switcher */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
        <div className="flex justify-center">
          <LanguageSwitcher />
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Trading Coach v1.0
        </p>
      </div>
    </aside>
  );
}
