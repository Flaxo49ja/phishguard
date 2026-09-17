import { useCallback, useState } from 'react';
import { classifyUrl, isValidUrl, SAMPLE_URLS } from '../lib/classifier';
import type { ClassificationResult } from '../lib/classifier';
import VerdictCard from './VerdictCard';
import ContributionList from './ContributionList';
import FeatureGrid from './FeatureGrid';
import SampleUrls from './SampleUrls';
import HistoryList from './HistoryList';

export interface AnalysisResult extends ClassificationResult {
  url: string;
  timestamp: Date;
}

export default function UrlChecker() {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>([]);

  const analyze = useCallback((input?: string) => {
    const target = (input ?? url).trim();
    if (!target) { setError('Enter a URL to analyze.'); return; }
    if (!isValidUrl(target)) { setError('Enter a valid URL, e.g. https://example.com'); return; }
    setError('');
    const analysis: AnalysisResult = { ...classifyUrl(target), url: target, timestamp: new Date() };
    setResult(analysis);
    setHistory((prev) => [analysis, ...prev].slice(0, 10));
  }, [url]);

  const selectHistory = (item: AnalysisResult) => { setUrl(item.url); setResult(item); };

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="space-y-3 py-6 text-center">
        <h2 className="bg-gradient-to-r from-red-400 via-orange-400 to-amber-300 bg-clip-text text-3xl font-bold text-transparent md:text-5xl">
          Is this URL safe to open?
        </h2>
        <p className="mx-auto max-w-2xl text-slate-400">
          A real machine-learning model — trained on 107,355 URLs — runs entirely in your browser.
          18 lexical features, zero network calls.
        </p>
      </div>

      {/* Input */}
      <div className="mx-auto max-w-3xl">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <label htmlFor="url-input" className="mb-2 block text-sm font-medium text-slate-300">
            URL to analyze
          </label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              id="url-input"
              type="text"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setError(''); }}
              onKeyDown={(e) => { if (e.key === 'Enter') analyze(); }}
              placeholder="https://example.com/login"
              className="w-full rounded-xl border border-white/10 bg-slate-900/80 px-4 py-3 font-mono text-sm text-slate-100 placeholder-slate-500 outline-none transition focus:border-orange-500/50 focus:ring-2 focus:ring-orange-500/30"
            />
            <button
              onClick={() => analyze()}
              className="shrink-0 rounded-xl bg-gradient-to-r from-red-500 to-orange-500 px-6 py-3 font-semibold text-white shadow-lg shadow-red-500/20 transition active:scale-95 hover:shadow-orange-500/40"
            >
              Analyze
            </button>
          </div>
          {error && <p className="mt-3 text-sm text-red-400" role="alert">{error}</p>}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="animate-rise mx-auto max-w-3xl space-y-4">
          <VerdictCard result={result} />
          <ContributionList result={result} />
          <FeatureGrid result={result} />
        </div>
      )}

      <SampleUrls onPick={analyze} />
      <HistoryList history={history.slice(1)} onSelect={selectHistory} />
    </div>
  );
}
