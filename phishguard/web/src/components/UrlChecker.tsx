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
    <div className="space-y-10">
      {/* Hero */}
      <div className="space-y-2 pt-4">
        <h2 className="max-w-3xl text-4xl font-black uppercase leading-[1.05] tracking-tight text-black md:text-6xl">
          Is this URL safe to open?
        </h2>
        <p className="max-w-2xl border-l-4 border-black pl-4 text-neutral-700">
          A real machine-learning model — trained on 107,355 URLs — runs entirely in your browser.
          18 lexical features, zero network calls.
        </p>
      </div>

      {/* Input */}
      <div className="max-w-3xl">
        <div className="border-2 border-black p-5">
          <label htmlFor="url-input" className="mb-2 block font-mono text-xs font-bold uppercase tracking-wider text-neutral-700">
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
              className="w-full border-2 border-black bg-white px-4 py-3 font-mono text-sm text-black placeholder-neutral-400 outline-none focus:bg-neutral-100"
            />
            <button
              onClick={() => analyze()}
              className="shrink-0 border-2 border-black bg-black px-6 py-3 font-mono text-sm font-bold uppercase tracking-wider text-white transition-colors hover:bg-white hover:text-black active:translate-y-[2px]"
            >
              Analyze
            </button>
          </div>
          {error && <p className="mt-3 font-mono text-sm text-red-700" role="alert">{error}</p>}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="max-w-3xl space-y-6">
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
