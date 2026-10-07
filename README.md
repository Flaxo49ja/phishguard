# PhishGuard

[![Tests](https://github.com/Flaxo49ja/phishguard/actions/workflows/ci.yml/badge.svg)](https://github.com/Flaxo49ja/phishguard/actions/workflows/ci.yml)

Machine-learning phishing URL detection — **as a website**. Paste a URL, get an
instant verdict with a feature-by-feature explanation. The trained model runs
entirely in your browser: **no server, no network calls at inference time — the
URL you paste never leaves the page.**

Full details live in [`phishguard/README.md`](phishguard/README.md) (site +
model) and [`phishguard/training/README.md`](phishguard/training/README.md)
(Python pipeline & metrics).

## How it works

1. **18 lexical/structural features** are extracted from the URL string only —
   length, entropy, subdomain count, TLD-in-subdomain, shorteners, IP hosts,
   `@`-symbols, and more. No page content is fetched.
2. A **LogisticRegression trained in Python** on **107,355 real URLs**
   (48,338 verified PhishTank phishing + 59,017 legitimate Tranco/benign deep
   links) is exported to a ~2 KB JSON file and reproduced exactly in the
   browser: `p = sigmoid(bias + Σ wᵢ·(xᵢ − meanᵢ)/stdᵢ)`.
3. Each verdict is explained by **occlusion**: how much does the phishing
   probability change when one feature is swapped to a benign-typical value?
4. A RandomForest (test F1 0.888, ROC-AUC 0.954) outperformed LR (F1 0.804),
   but can't be exported to a browser losslessly — its per-feature importances
   are shown in the UI.

## Run the site

```bash
git clone https://github.com/Flaxo49ja/phishguard.git
cd phishguard/phishguard/web
npm install
npm run dev        # http://localhost:3000
```

Production build: `npm run build` → deploy `web/dist/` to any static host.

## Retrain (keeps the site in sync)

```bash
cd phishguard/training
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.train   # trains, evaluates, re-exports the web model to web/src/model/
```

## Tests

- **Web:** `cd phishguard/web && npm test` — 17 Vitest cases, including
  golden-master tests that pin the browser model's output to the Python CLI's
  LogisticRegression output for 8 URLs.
- **Python:** `cd phishguard/training && python src/features_test.py`
  (stdlib-only); CLI regression suite when scikit-learn is installed.

## Ethics & limits

The model favors recall (missing phishing costs more than a false alarm) and
inspects only the URL text — not page content, domain age, or reputation.
Educational/defensive use: **never block a URL on this verdict alone.**

## License

No license yet — all rights reserved by default. Ask before reusing the code.
