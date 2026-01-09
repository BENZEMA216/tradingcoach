import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function Layout() {
  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-black text-slate-900 dark:text-white flex transition-colors duration-200">
      <Sidebar />
      {/* Main content - responsive margin: no margin on mobile (sidebar is hidden), ml-64 on md+ */}
      <main className="flex-1 ml-0 md:ml-64 p-4 md:p-8 pt-[70px] md:pt-8 bg-neutral-50 dark:bg-black transition-colors duration-200">
        <Outlet />
      </main>
    </div>
  );
}
