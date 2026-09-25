import { FEATURE_DESCRIPTIONS } from '../lib/features';

export default function FeatureReference() {
  const entries = Object.entries(FEATURE_DESCRIPTIONS);
  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h2 className="text-4xl font-black uppercase tracking-tight text-black">Feature reference</h2>
        <p className="mt-2 border-l-4 border-black pl-4 text-neutral-700">
          The same 18 features the model was trained on — computed identically in Python and in your browser.
        </p>
      </div>
      <div className="border-2 border-black">
        {entries.map(([name, desc], i) => (
          <div key={name} className={`flex items-start gap-3 px-4 py-3 ${i > 0 ? 'border-t border-neutral-300' : ''} ${i % 2 === 0 ? 'bg-neutral-50' : 'bg-white'}`}>
            <span className="w-7 shrink-0 font-mono text-xs font-bold text-neutral-500">{String(i + 1).padStart(2, '0')}</span>
            <div>
              <div className="font-mono text-sm font-bold text-black">{name}</div>
              <div className="mt-0.5 text-xs text-neutral-600">{desc}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="border-2 border-amber-700 border-l-8 bg-amber-50 p-5">
        <h3 className="mb-1 font-mono text-sm font-bold uppercase tracking-wider text-amber-800">Deliberately excluded: domain age</h3>
        <p className="text-sm text-neutral-700">
          WHOIS lookups require network access and break the offline guarantee — excluded by design.
        </p>
      </div>
    </div>
  );
}
