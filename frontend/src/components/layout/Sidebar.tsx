import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import {
  List,
  BarChart3,
  TrendingUp,
  Calendar,
  Upload,
  Home,
  Monitor,
  Menu,
  X,
} from 'lucide-react';
import clsx from 'clsx';
import { LanguageSwitcher, ThemeToggle } from '@/components/common';

// Main navigation items
const navItems = [
  { to: '/statistics', icon: BarChart3, labelKey: 'nav.statistics' },
  { to: '/positions', icon: List, labelKey: 'nav.positions' },
  { to: '/events', icon: Calendar, labelKey: 'nav.events' },
];

export function Sidebar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  // Close mobile menu when clicking outside or pressing escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsMobileMenuOpen(false);
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  return (
    <>
      {/* Mobile Header with Hamburger Menu */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-14 bg-white dark:bg-black border-b border-neutral-200 dark:border-white/10 z-50 flex items-center px-4">
        <button
          onClick={() => setIsMobileMenuOpen(true)}
          className="p-2 -ml-2 text-slate-600 dark:text-white/70 hover:text-slate-900 dark:hover:text-white"
          aria-label={t('common.menu', 'Menu')}
        >
          <Menu className="w-6 h-6" />
        </button>
        <div className="flex items-center ml-3">
          <div className="w-6 h-6 bg-black dark:bg-white text-white dark:text-black flex items-center justify-center rounded-sm mr-2">
            <TrendingUp className="w-4 h-4" />
          </div>
          <span className="text-xs font-mono font-bold tracking-widest text-slate-900 dark:text-white uppercase">
            TC_TERMINAL
          </span>
        </div>
      </header>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-50"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        "fixed left-0 top-0 h-screen w-64 bg-white dark:bg-black border-r border-neutral-200 dark:border-white/10 flex flex-col z-50 transition-all duration-300",
        // Mobile: hidden by default, slide in when open
        "md:translate-x-0",
        isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Industrial Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-neutral-200 dark:border-white/10">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-black dark:bg-white text-white dark:text-black flex items-center justify-center rounded-sm mr-3">
              <TrendingUp className="w-5 h-5" />
            </div>
            <span className="text-sm font-mono font-bold tracking-widest text-slate-900 dark:text-white uppercase">
              TC_TERMINAL
            </span>
          </div>
          {/* Mobile Close Button */}
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="md:hidden p-2 -mr-2 text-slate-600 dark:text-white/70 hover:text-slate-900 dark:hover:text-white"
            aria-label={t('common.close', 'Close')}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Home Button */}
        <div className="px-3 pt-6">
          <button
            onClick={() => navigate('/')}
            className="w-full flex items-center px-4 py-3 rounded-sm text-sm font-mono text-slate-500 dark:text-white/60 hover:text-slate-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-white/5 transition-all duration-200 border border-transparent hover:border-neutral-200 dark:hover:border-white/10"
          >
            <Home className="w-4 h-4 mr-3" />
            <span className="uppercase tracking-wide">{t('nav.home', 'HOME BASE')}</span>
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-6 px-3 space-y-8">
          <div>
            <p className="px-4 mb-3 text-[10px] font-mono font-bold text-slate-400 dark:text-white/30 uppercase tracking-[0.2em]">
              {t('nav.analysis', 'MODULES')}
            </p>
            <ul className="space-y-1">
              {navItems.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    className={({ isActive }) =>
                      clsx(
                        'flex items-center px-4 py-3 rounded-none text-sm font-medium transition-all duration-200 border-l-2',
                        isActive
                          ? 'bg-neutral-100 dark:bg-white text-black border-black dark:border-white shadow-sm dark:shadow-[0_0_15px_rgba(255,255,255,0.1)]'
                          : 'border-transparent text-slate-500 dark:text-white/50 hover:bg-neutral-50 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white hover:border-neutral-300 dark:hover:border-white/20'
                      )
                    }
                  >
                    <item.icon className={clsx("w-5 h-5 mr-3", ({ isActive }: { isActive: boolean }) => isActive ? "text-black" : "text-slate-400 dark:text-white/50")} />
                    <span className="uppercase tracking-wide font-mono text-xs">{t(item.labelKey)}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>

          {/* Data Management */}
          <div>
            <p className="px-4 mb-3 text-[10px] font-mono font-bold text-slate-400 dark:text-white/30 uppercase tracking-[0.2em]">
              DATA_LINK
            </p>
            <button
              onClick={() => navigate('/')}
              className="w-full flex items-center px-4 py-3 rounded-sm text-sm font-medium text-slate-500 dark:text-white/50 hover:bg-neutral-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white transition-all duration-200"
            >
              <Upload className="w-5 h-5 mr-3 text-slate-400 dark:text-white/50" />
              <span className="uppercase tracking-wide font-mono text-xs">{t('nav.uploadNew', 'IMPORT CSV')}</span>
            </button>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-6 border-t border-neutral-200 dark:border-white/10 space-y-4 bg-white dark:bg-black">
          <div className="flex justify-center gap-4 opacity-70 hover:opacity-100 transition-opacity">
            <ThemeToggle />
            <LanguageSwitcher />
          </div>
          <div className="flex items-center justify-center space-x-2 text-[10px] uppercase tracking-widest text-slate-400 dark:text-white/20 font-mono">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>SYSTEM ONLINE v1.0</span>
          </div>
        </div>
      </aside>
    </>
  );
}
