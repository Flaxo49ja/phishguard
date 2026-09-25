import type { AnalysisResult } from './UrlChecker';

const verdictTheme = {
  PHISHING: {
    border: 'border-red-700',
    text: 'text-red-700',
    bar: 'bg-red-700',
    chip: 'bg-red-700 text-white',
  },
  LEGITIMATE: {
    border: 'border-green-700',
    text: 'text-green-700',
    bar: 'bg-green-700',
    chip: 'bg-green-700 text-white',
  },
} as const;

export default function VerdictCard({ result }: { result: AnalysisResult }) {
  const theme = verdictTheme[result.verdict];
  const pct = (result.probability * 100).toFixed(1);
  return (
    <div className={`border-2 border-black ${theme.border} border-l-8 p-5`}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <span className={`px-2 py-1 font-mono text-sm font-bold uppercase tracking-wider ${theme.chip}`}>
            {result.verdict}
          </span>
          <p className="text-sm text-neutral-700">
            Confidence: {result.confidence} · {(result.probability * 100).toFixed(1)}% phishing
          </p>
        </div>
        <div className={`font-mono text-3xl font-bold ${theme.text}`}>{pct}%</div>
      </div>
      <div className="mt-4 h-4 border-2 border-black">
        <div className={`h-full ${theme.bar}`} style={{ width: `${result.probability * 100}%` }} />
      </div>
      <p className="mt-2 font-mono text-xs text-neutral-600">
        Benign baseline: {(result.benignBaselineProbability * 100).toFixed(1)}% — what the model would predict if every feature looked benign-typical.
      </p>
      <div className="mt-4 border-t-2 border-black pt-3">
        <div className="font-mono text-xs font-bold uppercase tracking-wider text-neutral-600">Analyzed URL</div>
        <div className="break-all font-mono text-sm text-black">{result.url}</div>
      </div>
    </div>
  );
}
