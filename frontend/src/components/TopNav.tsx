import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Activity, ShieldCheck, ShieldAlert, Wifi, RefreshCw } from 'lucide-react';

interface TopNavProps {
  currentPageTitle: string;
  onRefresh?: () => void;
}

export const TopNav: React.FC<TopNavProps> = ({ currentPageTitle, onRefresh }) => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [checking, setChecking] = useState<boolean>(false);

  const checkStatus = async () => {
    setChecking(true);
    try {
      const data = await api.getHealth();
      setIsHealthy(data.status === 'healthy');
    } catch {
      setIsHealthy(false);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-slate-900/60 backdrop-blur border-b border-slate-800 px-8 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center space-x-3">
        <h2 className="text-lg font-semibold text-white tracking-wide">
          {currentPageTitle}
        </h2>
      </div>

      <div className="flex items-center space-x-4">
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition text-xs flex items-center gap-1.5 px-2.5"
            title="Refresh View"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync</span>
          </button>
        )}

        {/* Backend health status badge */}
        <div
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
            isHealthy === true
              ? 'bg-emerald-950/60 border-emerald-800/80 text-emerald-400'
              : isHealthy === false
              ? 'bg-red-950/60 border-red-800/80 text-red-400'
              : 'bg-slate-800 border-slate-700 text-slate-400'
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isHealthy === true
                ? 'bg-emerald-400 animate-pulse'
                : isHealthy === false
                ? 'bg-red-500'
                : 'bg-slate-400'
            }`}
          />
          <span>
            {checking
              ? 'Checking...'
              : isHealthy === true
              ? 'CSMS Core Online'
              : isHealthy === false
              ? 'CSMS Offline'
              : 'Connecting...'}
          </span>
        </div>

        <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-400 bg-slate-800/60 px-2.5 py-1.5 rounded-lg border border-slate-700/50">
          <Wifi className="w-3.5 h-3.5 text-cyan-400" />
          <span>Local Simulation Sandbox</span>
        </div>
      </div>
    </header>
  );
};
