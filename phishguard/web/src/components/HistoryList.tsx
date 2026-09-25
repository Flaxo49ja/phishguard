import type { AnalysisResult } from './UrlChecker';

export default function HistoryList({ history, onSelect }: { history: AnalysisResult[]; onSelect: (item: AnalysisResult) => void }) {
  if (history.length === 0) return null;
  return (
    <div className="max-w-3xl">
      <h3 className="mb-3 border-b-2 border-black pb-1 font-mono text-sm font-bold uppercase tracking-wider">Recent analyses</h3>
      <div className="divide-y-2 divide-black border-2 border-black">
        {history.map((item, i) => (
          <button
            key={`${item.url}-${i}`}
            onClick={() => onSelect(item)}
            className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-neutral-200"
          >
            <span className="max-w-md truncate font-mono text-xs text-neutral-700">{item.url}</span>
            <span className={`font-mono text-xs font-bold uppercase ${item.verdict === 'PHISHING' ? 'text-red-700' : 'text-green-700'}`}>
              {item.verdict} · {(item.probability * 100).toFixed(0)}%
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
