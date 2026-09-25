import { useState } from 'react';
import type { AnalysisResult } from './UrlChecker';

const riskColor = { high: 'text-red-700', medium: 'text-amber-700', low: 'text-green-700', neutral: 'text-neutral-600' } as const;
const riskBg = { high: 'bg-red-100', medium: 'bg-amber-100', low: 'bg-green-100', neutral: 'bg-white' } as const;

export default function FeatureGrid({ result }: { result: AnalysisResult }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(result.allFeatures);
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="w-full border-2 border-black bg-white py-3 font-mono text-sm font-bold uppercase tracking-wider transition-colors hover:bg-neutral-200"
      >
        {open ? 'Hide' : 'Show'} all 18 extracted features
      </button>
      {open && (
        <div className="mt-3 grid grid-cols-1 gap-0 border-2 border-black sm:grid-cols-2">
          {entries.map(([name, data], i) => (
            <div
              key={name}
              className={`flex items-center justify-between gap-2 border-b border-neutral-300 px-3 py-2 ${i % 2 === 0 ? 'sm:border-r' : ''} ${riskBg[data.risk as keyof typeof riskBg] ?? riskBg.neutral}`}
            >
              <span className="text-xs text-black">{name.replace(/_/g, ' ')}</span>
              <span className={`font-mono text-xs font-bold ${riskColor[data.risk as keyof typeof riskColor] ?? riskColor.neutral}`}>
                {typeof data.value === 'boolean' ? (data.value ? 'yes' : 'no') : data.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
