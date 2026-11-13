import React from 'react';

interface JsonViewerProps {
  data: any;
  maxHeight?: string;
  title?: string;
}

export const JsonViewer: React.FC<JsonViewerProps> = ({
  data,
  maxHeight = 'max-h-96',
  title,
}) => {
  const jsonString = typeof data === 'string' ? data : JSON.stringify(data, null, 2);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden shadow-inner">
      {title && (
        <div className="px-4 py-2 bg-slate-900 border-b border-slate-800/80 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-300 font-semibold">{title}</span>
          <span className="text-[10px] font-mono text-slate-500 uppercase">JSON UTF-8</span>
        </div>
      )}
      <pre
        className={`p-4 text-xs font-mono text-cyan-300/90 overflow-x-auto overflow-y-auto leading-relaxed ${maxHeight} selection:bg-blue-900 selection:text-white`}
      >
        <code>{jsonString}</code>
      </pre>
    </div>
  );
};
