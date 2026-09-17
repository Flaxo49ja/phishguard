const cards = [
  {
    title: 'Problem',
    body: 'Phishing URLs mimic legitimate services to steal credentials. PhishGuard classifies a URL using only its own text — 18 lexical and structural features — with no network calls, DNS, or WHOIS.',
  },
  {
    title: 'Dataset',
    body: '107,355 real URLs: 48,338 verified phishing (PhishTank) + 59,017 legitimate (Tranco top-10k + real benign deep links). Deduplicated, capped at 10 URLs per host so the model learns transferable patterns instead of memorizing hosts.',
  },
  {
    title: 'Model',
    body: 'LogisticRegression (F1 0.80) and RandomForest (F1 0.89) were trained in Python with scikit-learn on an 80/20 stratified split. The LR pipeline is exported to JSON and reproduced exactly in your browser.',
  },
  {
    title: 'Ethics',
    body: 'Missing phishing (false negative) is costlier than a false alarm, so the model is tuned for recall. Verdicts are informational: never rely on one tool for security decisions, and always allow human override.',
  },
];

export default function Methodology() {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h2 className="text-3xl font-bold text-white">Methodology</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {cards.map((c) => (
          <section key={c.title} className="rounded-2xl border border-white/10 bg-white/5 p-6">
            <h3 className="mb-2 font-semibold text-white">{c.title}</h3>
            <p className="text-sm leading-relaxed text-slate-400">{c.body}</p>
          </section>
        ))}
      </div>
      <section className="rounded-2xl border border-amber-500/20 bg-amber-950/20 p-6">
        <h3 className="mb-2 font-semibold text-amber-400">Limitations</h3>
        <p className="text-sm leading-relaxed text-slate-400">
          Lexical features cannot see page content, domain age, or reputation. Clean-looking phishing URLs may pass.
          The model reflects its training data and needs retraining as tactics evolve.
        </p>
      </section>
    </div>
  );
}
