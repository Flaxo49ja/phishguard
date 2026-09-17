import type { AnalysisResult } from './UrlChecker';

const verdictTheme = {
  PHISHING: {
    card: 'border-red-500/30 bg-red-950/40',
    icon: 'bg-red-500/15 text-red-400',
    text: 'text-red-400',
    bar: 'from-red-600 to-red-400',
  },
  LEGITIMATE: {
    card: 'border-emerald-500/30 bg-emerald-950/40',
    icon: 'bg-emerald-500/15 text-emerald-400',
    text: 'text-emerald-400',
    bar: 'from-emerald-600 to-emerald-400',
  },
} as const;

export default function VerdictCard({ result }: { result: AnalysisResult }) {
  const theme = verdictTheme[result.verdict];
  const pct = (result.probability * 100).toFixed(1);
  return (
    <div className={`animate-rise rounded-2xl border p-6 ${theme.card}`}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className={`flex h-12 w-12 items-center justify-center rounded-full text-2xl ${theme.icon}`}>
            {result.verdict === 'PHISHING' ? '⚠' : '✓'}
          </div>
          <div>
            <h3 className={`text-2xl font-bold ${theme.text}`}>{result.verdict}</h3>
            <p className="text-sm text-slate-400">
              Confidence: {result.confidence} · {(result.probability * 100).toFixed(1)}% phishing
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className={`font-mono text-3xl font-bold ${theme.text}`}>{pct}%</div>
        </div>
      </div>
      <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-800">
        <div className={`animate-bar h-full rounded-full bg-gradient-to-r ${theme.bar}`} style={{ width: `${result.probability * 100}%` }} />
      </div>
      <p className="mt-2 text-xs text-slate-500">
        Benign baseline: {(result.benignBaselineProbability * 100).toFixed(1)}% — what the model would predict if every feature looked benign-typical.
      </p>
      <div className="mt-4 rounded-xl border border-white/5 bg-slate-900/60 p-3">
        <div className="text-xs text-slate-500">Analyzed URL</div>
        <div className="break-all font-mono text-sm text-slate-300">{result.url}</div>
      </div>
    </div>
  );
}
