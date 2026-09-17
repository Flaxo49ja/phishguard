# PhishGuard Consolidation & Site Remake — Design Spec

**Date:** 2026-09-17
**Status:** Approved by user in chat (design Q&A + approval gate)

## Goal

Turn the split project (`phishing-detector/` Python CLI + `workspace/` React demo) into **one well-arranged folder** where the **website is the primary product** and the real trained ML model runs **in the browser**.

## Non-Goals

- No server/backend: predictions stay client-side (static deploy).
- No RandomForest in the browser (53 MB forest can't be exported losslessly); it stays a Python-side/training artifact shown via metrics + feature importances.
- No changes to feature extraction semantics, model weights, or training pipeline behavior.

## Target Layout

```
phishguard/
├── README.md                 # NEW: site-first README
├── .gitignore                # merged (python + node)
├── web/                      # THE SITE — primary deliverable
│   ├── index.html            # cleaned: lang=en, no sandbox scripts, no FA CDN
│   ├── package.json          # name: phishguard-web; adds "test": "vitest run"
│   ├── vite.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx           # slim shell: header/nav/tabs/footer
│       ├── components/       # one component per UI section
│       │   ├── UrlChecker.tsx
│       │   ├── VerdictCard.tsx
│       │   ├── ContributionList.tsx
│       │   ├── FeatureGrid.tsx
│       │   ├── HistoryList.tsx
│       │   ├── SampleUrls.tsx
│       │   ├── Methodology.tsx
│       │   ├── FeatureReference.tsx
│       │   └── ResultsPanel.tsx   # metrics table, confusion matrix, importances, class balance
│       ├── lib/              # logic, framework-free, testable
│       │   ├── features.ts        # (moved) 18-feature extraction, Python-parity
│       │   ├── modelLoader.ts     # (moved) exported LR pipeline inference + occlusion
│       │   ├── classifier.ts      # (moved) classifyUrl façade
│       │   ├── sampleUrls.ts      # (moved)
│       │   ├── check_url_golden.json  # golden-master fixture (copied from training/src/)
│       │   ├── features.test.ts   # vitest: feature extraction parity cases
│       │   └── classifier.test.ts # vitest: golden-master probability/verdict parity
│       └── model/
│           ├── lrModel.json            # REAL trained pipeline (browser inference)
│           └── rfFeatureImportances.json
└── training/                 # Python ML pipeline (moved from phishing-detector/, behavior unchanged)
    ├── README.md             # former project README, paths patched
    ├── requirements.txt
    ├── make_guide_pdf.py
    ├── src/                  # features, train, evaluate, fetch_data, export_model, check_url(+tests)
    ├── models/               # *.pkl, lr_fast.json
    ├── data/                 # raw + processed
    └── reports/
```

## Key Decisions

1. **Architecture: browser-only static site.** The exported LogisticRegression pipeline JSON (~2 KB: scaler means/stds, weights, bias) reproduces Python inference exactly (`z = bias + Σ w_i·(x_i−mean_i)/std_i; p = sigmoid(z)`). Instant, offline-capable, deployable to any static host. User confirmed "one that uses the model is priority."
2. **One folder:** `phishguard/` with `web/` + `training/`. `workspace/.git` (auto-snapshot commits only) is dropped — user approved. `AI-project.zip` untouched.
3. **Design: dark security console (evolved).** Slate-950 base, red→orange gradient accents, mono type for URLs, glass cards (`bg-white/5 border-white/10 backdrop-blur`), consistent rounded-xl, mobile-first responsive. Single-page tab navigation: Checker / Methodology / Features / Results.
4. **Correctness is tested:** vitest golden-master tests assert the browser model reproduces the pinned Python CLI outputs (probability within 5e-4, verdict identical, all 18 features identical).
5. **Retraining stays in sync:** `training/src/export_model.py` output path changes to `../web/src/model/`.

## Error Handling

- Invalid/empty URL input → inline error message (no crash); `isValidUrl` regex unchanged.
- Malformed URLs in feature extraction → parse fallback (existing behavior, unchanged).
- Missing training report at export time → nulls (existing behavior, unchanged).

## Testing

- **Web (vitest):** feature-extraction parity cases (entropy, IP host, ccTLD exemption, shorteners, @-handling) + golden-master parity for 8 pinned URLs (probability, verdict, features, benign baseline).
- **Typecheck:** `tsc --noEmit`. **Build:** `vite build`.
- **Python:** `training/src/features_test.py` still passes with system python3 (pure stdlib); heavy sklearn tests require re-created venv (documented, not automated here — `.venv` is not moved).

## UI Sections (remake scope)

- **Checker:** hero, URL input with inline validation, verdict card (verdict, probability gauge, benign-baseline note), top-contributing-features list with directional bars, expandable all-18-features grid, sample URLs (phishing/legit), recent-analyses history.
- **Methodology:** problem, dataset (107,355 real URLs), feature engineering, training, ethics (FP/FN trade-off).
- **Features:** all 18 features with descriptions + excluded-feature callout.
- **Results:** LR vs RF metrics table, confusion matrix (RF), feature importance bars, class distribution.
