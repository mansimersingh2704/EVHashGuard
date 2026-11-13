import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const norm = (status || '').toUpperCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';

  if (norm === 'RECOMMENDED' || norm === 'PASS' || norm === 'SECURE' || norm === 'LOW' || norm === 'SUCCESS' || norm === 'DETECTED') {
    colorClasses = 'bg-emerald-950/70 text-emerald-400 border-emerald-800/80';
  } else if (norm === 'WEAK' || norm === 'MEDIUM' || norm === 'WARNING' || norm === 'PENDING') {
    colorClasses = 'bg-amber-950/70 text-amber-400 border-amber-800/80';
  } else if (norm === 'BROKEN' || norm === 'FAIL' || norm === 'CRITICAL' || norm === 'HIGH' || norm === 'UNDETECTED' || norm === 'ERROR') {
    colorClasses = 'bg-rose-950/70 text-rose-400 border-rose-800/80';
  } else if (norm === 'MIGRATED' || norm === 'ENVELOPED') {
    colorClasses = 'bg-blue-950/70 text-blue-400 border-blue-800/80';
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${colorClasses} ${className}`}
    >
      {norm}
    </span>
  );
};
