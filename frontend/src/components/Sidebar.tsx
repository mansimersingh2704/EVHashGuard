import React from 'react';
import {
  LayoutDashboard,
  FlaskConical,
  Zap,
  Radio,
  ShieldAlert,
  ArrowUpCircle,
  Bug,
  AlertTriangle,
  FileText,
  BookOpen,
  ShieldCheck,
} from 'lucide-react';

interface SidebarProps {
  currentPage: string;
  onSelectPage: (page: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onSelectPage }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'hash_lab', label: 'Hash Laboratory', icon: FlaskConical },
    { id: 'collision', label: 'Collision Analysis', icon: Zap },
    { id: 'ev_simulator', label: 'EV Simulator', icon: Radio },
    { id: 'legacy_md5', label: 'Legacy MD5', icon: ShieldAlert },
    { id: 'migration', label: 'SHA-3 Migration', icon: ArrowUpCircle },
    { id: 'attacks', label: 'Attack Simulator', icon: Bug },
    { id: 'risk', label: 'Risk Analysis', icon: AlertTriangle },
    { id: 'audit', label: 'Audit Logs', icon: FileText },
    { id: 'docs', label: 'Documentation', icon: BookOpen },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col fixed h-screen z-20">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center space-x-3 bg-slate-900/40">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-white text-base tracking-wide flex items-center gap-1.5">
            EVHashGuard
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800/60 text-cyan-400 font-mono">
              v1.0
            </span>
          </h1>
          <p className="text-[11px] text-slate-400 font-mono">OCPP 1.6 Crypto Guard</p>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-blue-600/90 text-white shadow-md shadow-blue-600/25 font-semibold'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/30 text-xs text-slate-500">
        <div className="flex items-center justify-between text-[11px] mb-1">
          <span className="text-slate-400">Cryptosystem:</span>
          <span className="font-mono text-cyan-400">SHA3-256</span>
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-slate-400">Protocol:</span>
          <span className="font-mono text-slate-300">OCPP 1.6-J</span>
        </div>
      </div>
    </aside>
  );
};
