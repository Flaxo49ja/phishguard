import type { AnalysisResult } from './UrlChecker';

export default function HistoryList({ history, onSelect }: { history: AnalysisResult[]; onSelect: (item: AnalysisResult) => void }) {
  if (history.length === 0) return null;
  return (
    <div className="mx-auto max-w-3xl">
      <h3 className="mb-3 font-semibold text-slate-300">Recent analyses</h3>
      <div className="space-y-2">
        {history.map((item, i) => (
          <button
            key={`${item.url}-${i}`}
            onClick={() => onSelect(item)}
            className={`flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left transition hover:brightness-125 ${
              item.verdict === 'PHISHING' ? 'border-red-500/20 bg-red-950/20' : 'border-emerald-500/20 bg-emerald-950/20'
            }`}
          >
            <span className="max-w-md truncate font-mono text-xs text-slate-400">{item.url}</span>
            <span className={`text-xs font-bold ${item.verdict === 'PHISHING' ? 'text-red-400' : 'text-emerald-400'}`}>
              {item.verdict} · {(item.probability * 100).toFixed(0)}%
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
