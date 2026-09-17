# PhishGuard

Machine-learning phishing URL detection — **as a website**. Paste a URL, get an
instant verdict explained feature-by-feature. The trained model runs entirely in
your browser: no server, no network calls, the URL you type never leaves the page.

## Quick start (the site)

```bash
cd web
npm install
npm run dev      # http://localhost:3000
```

Production build: `npm run build` → deploy `web/dist/` to any static host.

## How it works

- 18 lexical/structural features are extracted from the URL string (length,
  entropy, subdomains, TLD-in-subdomain, shorteners, IP hosts, @-symbols, …).
- A **LogisticRegression pipeline trained in Python** on **107,355 real URLs**
  (48,338 verified PhishTank phishing + 59,017 legitimate from Tranco and real
  benign deep links) is exported to JSON (~2 KB) and reproduced exactly in the
  browser: `p = sigmoid(bias + Σ wᵢ·(xᵢ − meanᵢ)/stdᵢ)`.
- Each verdict is explained by **occlusion**: how much does the phishing
  probability change when one feature is swapped to a benign-typical value?
- A RandomForest (test F1 0.888, ROC-AUC 0.954) outperformed LR (F1 0.804) but
  cannot be exported to a browser losslessly — its metrics and feature
  importances are shown on the Results tab.

## Layout

```
phishguard/
├── web/        # the site (React + Vite + TS + Tailwind) — primary deliverable
│   └── src/lib/       # feature extraction + model inference + tests
│   └── src/model/     # exported trained model JSON
└── training/   # Python pipeline: fetch data, train, evaluate, export, CLI
    └── src/check_url.py   # bonus CLI: python src/check_url.py <url>
```

## Retraining (keeps the site in sync)

```bash
cd training
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.fetch_data --custom   # requires raw datasets in data/raw/
python -m src.train                 # trains, evaluates, and re-exports the web model
```

`training/src/export_model.py` writes the refreshed pipeline straight to
`web/src/model/`, so a retrain automatically updates the site.

## Tests

- Web: `cd web && npm test` — feature-parity cases + golden-master tests that
  pin the browser model's outputs to the Python CLI's LogisticRegression
  outputs (generated via `python src/check_url.py <url> --json --fast`) for
  8 URLs: probability, verdict, all 18 features, benign baseline.
- Python: `cd training && python src/features_test.py` (stdlib-only), plus the
  CLI regression suite when scikit-learn is installed.

## Ethics & limits

Missing phishing is costlier than a false alarm, so the model favors recall.
It inspects only the URL text — not page content, domain age, or reputation —
and is for educational/defensive use. Never block a URL on this verdict alone.
