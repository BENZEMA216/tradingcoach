import { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';
import clsx from 'clsx';

export function ThemeToggle() {
    const [isDark, setIsDark] = useState(() => {
        if (typeof window === 'undefined') return true;
        return document.documentElement.classList.contains('dark') ||
            localStorage.getItem('theme') === 'dark' ||
            (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
    });

    useEffect(() => {
        if (isDark) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [isDark]);

    return (
        <button
            onClick={() => setIsDark(!isDark)}
            className={clsx(
                "p-2 rounded-sm transition-all duration-200 border",
                isDark
                    ? "bg-white/5 border-white/10 text-yellow-400 hover:bg-white/10"
                    : "bg-white border-neutral-200 text-orange-500 hover:bg-neutral-50 shadow-sm"
            )}
            title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
            {isDark ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </button>
    );
}
