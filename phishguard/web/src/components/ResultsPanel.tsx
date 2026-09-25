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
    <div className="max-w-4xl space-y-6">
      <div>
        <h2 className="text-4xl font-black uppercase tracking-tight text-black">Model performance</h2>
        <p className="mt-2 border-l-4 border-black pl-4 text-sm text-neutral-700">
          Measured on {REAL_METRICS.dataset.testSetSize.toLocaleString()} held-out URLs. Browser verdicts come from the
          exported LogisticRegression; RandomForest (the stronger model) is shown for comparison.
        </p>
      </div>

      {/* Metrics table */}
      <div className="border-2 border-black p-5">
        <h3 className="mb-4 font-mono text-sm font-bold uppercase tracking-wider">Metrics</h3>
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b-2 border-black text-left">
              <th className="py-2 pr-4 font-mono text-xs font-bold uppercase tracking-wider">Metric</th>
              <th className="py-2 pr-4 text-right font-mono text-xs font-bold uppercase tracking-wider">RandomForest</th>
              <th className="py-2 text-right font-mono text-xs font-bold uppercase tracking-wider">LogisticRegression</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.metric} className="border-b border-neutral-300 last:border-0">
                <td className="py-2.5 pr-4 text-black">{r.metric}</td>
                <td className="py-2.5 pr-4 text-right font-mono text-black">{r.rf}</td>
                <td className="py-2.5 text-right font-mono text-neutral-600">{r.lr}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Confusion matrix */}
      {cm && (
        <div className="border-2 border-black p-5">
          <h3 className="mb-4 font-mono text-sm font-bold uppercase tracking-wider">Confusion matrix — RandomForest</h3>
          <div className="mx-auto grid w-fit grid-cols-3 gap-1.5 text-center">
            <div />
            <div className="pb-1 font-mono text-xs font-bold uppercase text-neutral-600">pred. legit</div>
            <div className="pb-1 font-mono text-xs font-bold uppercase text-neutral-600">pred. phish</div>
            <div className="flex items-center pr-2 font-mono text-xs text-neutral-600">actual legit</div>
            <div className="flex h-24 w-24 flex-col items-center justify-center border-2 border-black bg-green-100">
              <span className="font-mono text-2xl font-bold text-green-800">{cm.tn.toLocaleString()}</span>
              <span className="font-mono text-xs text-green-800">TN</span>
            </div>
            <div className="flex h-24 w-24 flex-col items-center justify-center border-2 border-black bg-amber-100">
              <span className="font-mono text-2xl font-bold text-amber-800">{cm.fp.toLocaleString()}</span>
              <span className="font-mono text-xs text-amber-800">FP</span>
            </div>
            <div className="flex items-center pr-2 font-mono text-xs text-neutral-600">actual phish</div>
            <div className="flex h-24 w-24 flex-col items-center justify-center border-2 border-black bg-red-100">
              <span className="font-mono text-2xl font-bold text-red-800">{cm.fn.toLocaleString()}</span>
              <span className="font-mono text-xs text-red-800">FN</span>
            </div>
            <div className="flex h-24 w-24 flex-col items-center justify-center border-2 border-black bg-green-700">
              <span className="font-mono text-2xl font-bold text-white">{cm.tp.toLocaleString()}</span>
              <span className="font-mono text-xs text-white">TP</span>
            </div>
          </div>
        </div>
      )}

      {/* Feature importances */}
      <div className="border-2 border-black p-5">
        <h3 className="mb-4 font-mono text-sm font-bold uppercase tracking-wider">Feature importance — RandomForest (top 10)</h3>
        <div className="space-y-2.5">
          {importances.slice(0, 10).map(([name, imp], i) => (
            <div key={name} className="flex items-center gap-3">
              <span className="w-4 font-mono text-xs text-neutral-500">{i + 1}</span>
              <span className="w-44 truncate font-mono text-xs text-black">{name}</span>
              <div className="h-4 flex-1 border-2 border-black">
                <div className="h-full bg-black" style={{ width: `${(imp / maxImp) * 100}%` }} />
              </div>
              <span className="w-14 text-right font-mono text-xs text-neutral-600">{imp.toFixed(3)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Class balance */}
      <div className="border-2 border-black p-5">
        <h3 className="mb-4 font-mono text-sm font-bold uppercase tracking-wider">Dataset balance</h3>
        <div className="flex h-8 border-2 border-black">
          <div className="flex items-center justify-center bg-green-700 text-xs font-bold text-white" style={{ width: `${legitPct}%` }}>
            {legitPct}%
          </div>
          <div className="flex items-center justify-center bg-red-700 text-xs font-bold text-white" style={{ width: `${phishPct}%` }}>
            {phishPct}%
          </div>
        </div>
        <p className="mt-3 font-mono text-xs text-neutral-600">
          {REAL_METRICS.dataset.legitimate.toLocaleString()} legitimate vs {REAL_METRICS.dataset.phishing.toLocaleString()} phishing of {REAL_METRICS.dataset.totalUrls.toLocaleString()} total training URLs.
        </p>
      </div>
    </div>
  );
}
