import type { AnalysisResult } from './UrlChecker';
import { FEATURE_DESCRIPTIONS } from '../lib/features';

export default function ContributionList({ result }: { result: AnalysisResult }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
      <h4 className="mb-4 font-semibold text-white">Why this verdict</h4>
      <div className="space-y-2.5">
        {result.topContributingFeatures.map((f) => {
          const phish = f.contribution >= 0;
          const width = Math.min(Math.abs(f.contribution) * 120, 100);
          return (
            <div key={f.feature} className="flex items-center gap-3">
              <div className="w-40 shrink-0">
                <div className="text-sm text-slate-200">{f.feature.replace(/_/g, ' ')}</div>
                <div className="text-xs text-slate-500">{FEATURE_DESCRIPTIONS[f.feature]}</div>
              </div>
              <div className="relative h-6 flex-1 overflow-hidden rounded-md bg-slate-800/60">
                <div className={`h-full ${phish ? 'ml-auto bg-gradient-to-l from-red-500/70' : 'bg-gradient-to-r from-emerald-500/70'}`} style={{ width: `${width}%` }} />
              </div>
              <div className="w-28 shrink-0 text-right">
                <span className={`font-mono text-xs ${phish ? 'text-red-400' : 'text-emerald-400'}`}>
                  {phish ? '+' : ''}{f.contribution.toFixed(4)}
                </span>
                <span className="ml-2 text-xs text-slate-500">{String(f.value)}</span>
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-xs text-slate-500">
        Occlusion: change in phishing probability when the feature is swapped to a benign-typical value. Positive = pushed toward phishing.
      </p>
    </div>
  );
}
