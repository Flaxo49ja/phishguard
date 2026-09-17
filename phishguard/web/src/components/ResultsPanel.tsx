import { REAL_METRICS, RF_IMPORTANCES } from '../lib/modelLoader';

const rf = REAL_METRICS.randomForest;
const lr = REAL_METRICS.logisticRegression;
const fmt = (v: number | null) => (v === null ? '—' : v.toFixed(4));
const importances = Object.entries(RF_IMPORTANCES.importances);
const maxImp = importances[0]?.[1] ?? 1;
const cm = rf.confusion;

export default function ResultsPanel() {
  const rows: { metric: string; rf: string; lr: string }[] = [
    { metric: 'Precision', rf: fmt(rf.precision), lr: fmt(lr.precision) },
    { metric: 'Recall', rf: fmt(rf.recall), lr: fmt(lr.recall) },
    { metric: 'F1 score', rf: fmt(rf.f1), lr: fmt(lr.f1) },
    { metric: 'ROC-AUC', rf: fmt(rf.rocAuc), lr: fmt(lr.rocAuc) },
    { metric: '5-fold CV F1', rf: rf.cvF1 ?? '—', lr: lr.cvF1 ?? '—' },
  ];
  const legitPct = ((REAL_METRICS.dataset.legitimate / REAL_METRICS.dataset.totalUrls) * 100).toFixed(1);
  const phishPct = ((REAL_METRICS.dataset.phishing / REAL_METRICS.dataset.totalUrls) * 100).toFixed(1);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white">Model performance</h2>
        <p className="mt-2 text-sm text-slate-400">
          Measured on {REAL_METRICS.dataset.testSetSize.toLocaleString()} held-out URLs. Browser verdicts come from the
          exported LogisticRegression; RandomForest (the stronger model) is shown for comparison.
        </p>
      </div>

      {/* Metrics table */}
      <div className="overflow-x-auto rounded-2xl border border-white/10 bg-white/5 p-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-left text-slate-400">
              <th className="py-2 pr-4 font-medium">Metric</th>
              <th className="py-2 pr-4 text-right font-medium">RandomForest</th>
              <th className="py-2 text-right font-medium">LogisticRegression</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.metric} className="border-b border-white/5 last:border-0">
                <td className="py-2.5 pr-4 text-slate-300">{r.metric}</td>
                <td className="py-2.5 pr-4 text-right font-mono text-slate-200">{r.rf}</td>
                <td className="py-2.5 text-right font-mono text-slate-400">{r.lr}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Confusion matrix */}
      {cm && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="mb-4 font-semibold text-white">Confusion matrix — RandomForest</h3>
          <div className="mx-auto grid w-fit grid-cols-3 gap-1.5 text-center">
            <div />
            <div className="pb-1 text-xs text-slate-500">pred. legit</div>
            <div className="pb-1 text-xs text-slate-500">pred. phish</div>
            <div className="flex items-center pr-2 text-xs text-slate-500">actual legit</div>
            <div className="flex h-24 w-24 flex-col items-center justify-center rounded-xl border border-emerald-500/40 bg-emerald-500/10">
              <span className="text-2xl font-bold text-emerald-400">{cm.tn.toLocaleString()}</span>
              <span className="text-xs text-emerald-300/80">TN</span>
            </div>
            <div className="flex h-24 w-24 flex-col items-center justify-center rounded-xl border border-amber-500/30 bg-amber-500/5">
              <span className="text-2xl font-bold text-amber-400">{cm.fp.toLocaleString()}</span>
              <span className="text-xs text-amber-300/80">FP</span>
            </div>
            <div className="flex items-center pr-2 text-xs text-slate-500">actual phish</div>
            <div className="flex h-24 w-24 flex-col items-center justify-center rounded-xl border border-red-500/30 bg-red-500/5">
              <span className="text-2xl font-bold text-red-400">{cm.fn.toLocaleString()}</span>
              <span className="text-xs text-red-300/80">FN</span>
            </div>
            <div className="flex h-24 w-24 flex-col items-center justify-center rounded-xl border border-emerald-500/40 bg-emerald-500/10">
              <span className="text-2xl font-bold text-emerald-400">{cm.tp.toLocaleString()}</span>
              <span className="text-xs text-emerald-300/80">TP</span>
            </div>
          </div>
        </div>
      )}

      {/* Feature importances */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h3 className="mb-4 font-semibold text-white">Feature importance — RandomForest (top 10)</h3>
        <div className="space-y-2.5">
          {importances.slice(0, 10).map(([name, imp], i) => (
            <div key={name} className="flex items-center gap-3">
              <span className="w-4 text-xs text-slate-500">{i + 1}</span>
              <span className="w-44 truncate font-mono text-xs text-slate-300">{name}</span>
              <div className="h-5 flex-1 overflow-hidden rounded-full bg-slate-800/60">
                <div className="animate-bar h-full rounded-full bg-gradient-to-r from-red-500 to-orange-400" style={{ width: `${(imp / maxImp) * 100}%` }} />
              </div>
              <span className="w-14 text-right font-mono text-xs text-slate-400">{imp.toFixed(3)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Class balance */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h3 className="mb-4 font-semibold text-white">Dataset balance</h3>
        <div className="flex h-8 overflow-hidden rounded-full">
          <div className="flex items-center justify-center bg-gradient-to-r from-emerald-600 to-emerald-500 text-xs font-bold text-white" style={{ width: `${legitPct}%` }}>
            {legitPct}%
          </div>
          <div className="flex items-center justify-center bg-gradient-to-r from-red-500 to-red-600 text-xs font-bold text-white" style={{ width: `${phishPct}%` }}>
            {phishPct}%
          </div>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          {REAL_METRICS.dataset.legitimate.toLocaleString()} legitimate vs {REAL_METRICS.dataset.phishing.toLocaleString()} phishing of {REAL_METRICS.dataset.totalUrls.toLocaleString()} total training URLs.
        </p>
      </div>
    </div>
  );
}
