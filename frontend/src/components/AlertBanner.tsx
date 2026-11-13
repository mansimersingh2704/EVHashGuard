import React from 'react';
import { AlertTriangle, Info, CheckCircle2, XCircle } from 'lucide-react';

interface AlertBannerProps {
  type?: 'warning' | 'info' | 'success' | 'error';
  title?: string;
  message: string;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type = 'warning',
  title,
  message,
  className = '',
}) => {
  const styles = {
    warning: {
      bg: 'bg-amber-950/40 border-amber-800/80 text-amber-200',
      icon: AlertTriangle,
      iconColor: 'text-amber-400',
    },
    info: {
      bg: 'bg-cyan-950/40 border-cyan-800/80 text-cyan-200',
      icon: Info,
      iconColor: 'text-cyan-400',
    },
    success: {
      bg: 'bg-emerald-950/40 border-emerald-800/80 text-emerald-200',
      icon: CheckCircle2,
      iconColor: 'text-emerald-400',
    },
    error: {
      bg: 'bg-rose-950/40 border-rose-800/80 text-rose-200',
      icon: XCircle,
      iconColor: 'text-rose-400',
    },
  }[type];

  const Icon = styles.icon;

  return (
    <div className={`p-4 rounded-xl border flex items-start space-x-3 text-xs leading-relaxed ${styles.bg} ${className}`}>
      <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${styles.iconColor}`} />
      <div>
        {title && <h4 className="font-semibold text-white mb-0.5">{title}</h4>}
        <p className="text-slate-300">{message}</p>
      </div>
    </div>
  );
};
