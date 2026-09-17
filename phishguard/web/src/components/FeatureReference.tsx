import { FEATURE_DESCRIPTIONS } from '../lib/features';

export default function FeatureReference() {
  const entries = Object.entries(FEATURE_DESCRIPTIONS);
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white">Feature reference</h2>
        <p className="mt-2 text-slate-400">
          The same 18 features the model was trained on — computed identically in Python and in your browser.
        </p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {entries.map(([name, desc], i) => (
          <div key={name} className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-800 font-mono text-xs text-slate-400">{i + 1}</span>
            <div>
              <div className="font-mono text-sm text-slate-200">{name}</div>
              <div className="mt-0.5 text-xs text-slate-500">{desc}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-amber-500/20 bg-amber-950/20 p-6">
        <h3 className="mb-1 font-semibold text-amber-400">Deliberately excluded: domain age</h3>
        <p className="text-sm text-slate-400">
          WHOIS lookups require network access and break the offline guarantee — excluded by design.
        </p>
      </div>
    </div>
  );
}
