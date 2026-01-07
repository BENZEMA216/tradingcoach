import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function Layout() {
  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-black text-slate-900 dark:text-white flex transition-colors duration-200">
      <Sidebar />
      <main className="flex-1 ml-64 p-8 bg-neutral-50 dark:bg-black transition-colors duration-200">
        <Outlet />
      </main>
    </div>
  );
}
