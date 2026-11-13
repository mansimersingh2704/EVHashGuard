import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'blue' | 'emerald' | 'amber' | 'rose' | 'cyan';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'blue',
}) => {
  const colorMap = {
    blue: 'from-blue-600/20 to-blue-600/5 text-blue-400 border-blue-800/40',
    emerald: 'from-emerald-600/20 to-emerald-600/5 text-emerald-400 border-emerald-800/40',
    amber: 'from-amber-600/20 to-amber-600/5 text-amber-400 border-amber-800/40',
    rose: 'from-rose-600/20 to-rose-600/5 text-rose-400 border-rose-800/40',
    cyan: 'from-cyan-600/20 to-cyan-600/5 text-cyan-400 border-cyan-800/40',
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 relative overflow-hidden backdrop-blur-sm shadow-lg">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
          <h3 className="text-2xl font-bold text-white mt-1.5 font-mono">{value}</h3>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl bg-gradient-to-br border ${colorMap[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
