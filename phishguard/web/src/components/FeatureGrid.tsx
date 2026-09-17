import { useState } from 'react';
import type { AnalysisResult } from './UrlChecker';

const riskColor = { high: 'text-red-400', medium: 'text-amber-400', low: 'text-emerald-400', neutral: 'text-slate-400' } as const;
const riskBg = { high: 'border-red-500/25 bg-red-500/5', medium: 'border-amber-500/25 bg-amber-500/5', low: 'border-emerald-500/25 bg-emerald-500/5', neutral: 'border-white/5 bg-slate-800/30' } as const;

export default function FeatureGrid({ result }: { result: AnalysisResult }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(result.allFeatures);
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="w-full rounded-xl border border-white/10 py-3 text-sm text-slate-400 transition hover:bg-white/5 hover:text-slate-200"
      >
        {open ? 'Hide' : 'Show'} all 18 extracted features
      </button>
      {open && (
        <div className="animate-rise mt-3 grid grid-cols-1 gap-2 rounded-2xl border border-white/10 bg-white/5 p-4 sm:grid-cols-2">
          {entries.map(([name, data]) => (
            <div key={name} className={`flex items-center justify-between rounded-lg border px-3 py-2 ${riskBg[data.risk as keyof typeof riskBg] ?? riskBg.neutral}`}>
              <span className="text-xs text-slate-300">{name.replace(/_/g, ' ')}</span>
              <span className={`font-mono text-xs ${riskColor[data.risk as keyof typeof riskColor] ?? riskColor.neutral}`}>
                {typeof data.value === 'boolean' ? (data.value ? 'yes' : 'no') : data.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
