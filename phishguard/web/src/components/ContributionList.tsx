import type { AnalysisResult } from './UrlChecker';
import { FEATURE_DESCRIPTIONS } from '../lib/features';

export default function ContributionList({ result }: { result: AnalysisResult }) {
  return (
    <div className="border-2 border-black p-5">
      <h4 className="mb-4 border-b-2 border-black pb-2 font-mono text-sm font-bold uppercase tracking-wider">Why this verdict</h4>
      <div className="space-y-3">
        {result.topContributingFeatures.map((f) => {
          const phish = f.contribution >= 0;
          const width = Math.min(Math.abs(f.contribution) * 120, 100);
          return (
            <div key={f.feature} className="flex items-center gap-3">
              <div className="w-40 shrink-0">
                <div className="text-sm font-medium text-black">{f.feature.replace(/_/g, ' ')}</div>
                <div className="text-xs text-neutral-600">{FEATURE_DESCRIPTIONS[f.feature]}</div>
              </div>
              <div className="relative h-5 flex-1 border-2 border-black">
                <div
                  className={`h-full ${phish ? 'ml-auto bg-red-700' : 'bg-green-700'}`}
                  style={{ width: `${width}%` }}
                />
              </div>
              <div className="w-28 shrink-0 text-right">
                <span className={`font-mono text-xs font-bold ${phish ? 'text-red-700' : 'text-green-700'}`}>
                  {phish ? '+' : ''}{f.contribution.toFixed(4)}
                </span>
                <span className="ml-2 font-mono text-xs text-neutral-500">{String(f.value)}</span>
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-4 border-t border-neutral-300 pt-2 font-mono text-xs text-neutral-600">
        Occlusion: change in phishing probability when the feature is swapped to a benign-typical value. Positive = pushed toward phishing.
      </p>
    </div>
  );
}
