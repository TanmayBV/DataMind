import React from 'react';
import { Database, Sun, Moon, BookOpen, Activity, Menu } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useStore } from '../../context/StoreContext';
import { Badge, Button } from '../ui/Primitives';

interface TopbarProps {
  onOpenMobileSidebar?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onOpenMobileSidebar }) => {
  const { theme, toggleTheme } = useTheme();
  const { connection, apiLatencyMs, backendConnected } = useStore();

  return (
    <header className="sticky top-0 z-30 h-14 w-full bg-sidebar border-b border-border-subtle px-space-4 flex items-center justify-between transition-colors select-none">
      {/* Left: Mobile Menu & Brand Identity */}
      <div className="flex items-center gap-space-2">
        <button
          type="button"
          onClick={onOpenMobileSidebar}
          className="md:hidden p-1.5 -ml-1 text-secondary hover:text-primary hover:bg-card rounded-lg transition-colors cursor-pointer"
          aria-label="Open database and governance navigation"
          title="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="w-8 h-8 rounded-lg bg-accent-primary/10 border border-accent-primary/20 flex items-center justify-center text-accent-primary shrink-0">
          <Database className="w-5 h-5 text-accent-primary" />
        </div>
        <div className="flex items-center gap-1.5 sm:gap-2">
          <span className="text-base sm:text-lg font-semibold tracking-tight text-primary">
            DataMind
          </span>
          <Badge variant="neutral" className="text-[10px] sm:text-xs">
            v2.4
          </Badge>
        </div>
      </div>

      {/* Center: Live Connection Pill */}
      <div className="hidden md:flex items-center gap-space-2 px-space-4 py-1 rounded-full bg-card border border-border-subtle shadow-xs">
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              connection.status === 'connected'
                ? 'bg-status-success animate-pulse'
                : connection.status === 'connecting'
                ? 'bg-status-warning animate-pulse'
                : 'bg-status-error'
            }`}
          />
          <span className="text-xs font-semibold text-primary">
            {connection.displayName}
          </span>
        </div>

        <div className="h-3 w-[1px] bg-border-prominent" />

        <Badge
          variant={connection.status === 'connected' ? 'success' : 'neutral'}
          className="text-xs uppercase"
        >
          {connection.dialect}
        </Badge>

        <span className="text-xs text-secondary">
          {connection.tableCount} tables
        </span>
      </div>

      {/* Right: Actions, Health, Theme */}
      <div className="flex items-center gap-space-2">
        {/* API Latency Probe Badge */}
        <div
          className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-md bg-canvas text-secondary text-xs"
          title={backendConnected ? 'FastAPI Bridge Online' : 'FastAPI Bridge Unreachable'}
        >
          <Activity
            className={`w-3.5 h-3.5 ${
              backendConnected ? 'text-status-success' : 'text-status-error'
            }`}
          />
          <span>
            {apiLatencyMs !== null ? `${apiLatencyMs}ms` : backendConnected ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* Theme Toggle Button (44x44px target) */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? (
            <Sun className="w-5 h-5 text-amber-400" />
          ) : (
            <Moon className="w-5 h-5 text-slate-700" />
          )}
        </Button>

        {/* Documentation Link */}
        <a
          href="https://github.com/TanmayBV/DataMind"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] rounded-lg text-secondary hover:text-primary hover:bg-card transition-colors"
          aria-label="View DataMind documentation"
          title="Documentation"
        >
          <BookOpen className="w-5 h-5" />
        </a>
      </div>
    </header>
  );
};
