# Audit, Optimization & Design Decisions Report

**Project:** Phishing URL Detector (`phishing-detector/`) + PhishGuard web demo (`workspace/`)
**Scope:** Full audit of both projects — tests, CLI behaviour, model parity, performance — followed by targeted optimization of the CLI startup path.
**Result:** All 100 tests green (81 feature + 19 CLI), zero output changes from the refactor, and a new `--fast` mode that cuts CLI startup from ~20 s to **~0.65 s (~30×)** with identical verdicts.

---

## 1. What Was Audited and How

Every component was exercised, not just read:

| Check | Method | Result |
|---|---|---|
| Feature extraction correctness | Ran `src/features_test.py` | ✅ **81/81 pass** |
| CLI end-to-end behaviour | Ran `src/check_url.py` on 5 known URLs (2 legit, 3 phishing) and compared against the README's documented expected outputs | ✅ All 5 verdicts and probabilities match exactly |
| CLI flags | `--list-models`, `--json` | ✅ Both work; both trained pipelines load cleanly on Python 3.14 / scikit-learn 1.9 |
| Report consistency | Cross-checked `reports/training_report.json` vs `reports/metrics.json` | ✅ Internally consistent (RF F1 0.8878, LR F1 0.8043, 107,355 URLs, 21,471 test rows) |
| Web app typecheck | `npm run typecheck` in `workspace/` | ✅ Clean |
| Web app production build | `npm run build` | ✅ Clean (180 KB JS, 57 KB gzipped) |
| Python ↔ TypeScript feature parity | Extracted all 18 features for 10 URLs in both languages and diffed | ✅ Zero mismatches |
| Browser model parity | Ran the exported LR pipeline (browser JS) against the Python sklearn LR pipeline | ✅ Probabilities match **exactly to 6 decimal places** |
| Report generation scripts | Read `make_guide_pdf.py`, `evaluate.py` in full; verified the PDF path the script writes matches the file on disk | ✅ No path bugs |

---

## 2. Bugs and Issues Found

### 2.1 Nondeterministic CLI output (real bug — fixed)
**Symptom:** Running the CLI twice on the same URL could produce different JSON output — a per-feature contribution's `direction` field flipped between `'phishing'` and `'neutral'` for contributions that were essentially zero.

**Root cause:** RandomForest's parallel tree summation (`n_jobs=-1` via joblib) introduces float noise on the order of 1e-16 between runs. The explanation code derived `direction` from the *unrounded* contribution value, so a value like `-2.8e-17` (noise around zero) got labelled as a real push toward phishing on one run and neutral on the next.

**Why it matters:** Any consumer of `--json` output (tests, downstream tools, humans diffing results) would see flapping output for identical input. It also made the code impossible to regression-test with a golden master.

**Fix:** `direction` is now derived from the contribution value **after rounding** (same rounding applied to the reported number). Exact-zero contributions are now always and only ever `'neutral'`.

**Proof:** Diffed the old golden output against the new one — the *only* changed fields across all 8 pinned URLs were `direction` labels on exact-zero contributions (13 fields, all on `google.com`, all `'phishing' → 'neutral'`). Every probability, contribution, and feature value is byte-identical.

### 2.2 Warning spam on stderr (fixed)
**Symptom:** Every CLI run spewed dozens of sklearn `UserWarning`s to stderr, polluting output for any script consuming the CLI.

**Root cause:** `train.py` and `evaluate.py` already silenced warnings, but `check_url.py` — the one tool most likely to be embedded in other scripts — did not.

**Fix:** Matched the project convention: warnings are suppressed in the CLI. Verified: CLI stderr is now **0 bytes**.

### 2.3 Performance: ~20 s startup (fixed — see §3)

### 2.4 Test coverage gap (fixed)
The Python side had 81 feature unit tests but **zero tests for the CLI itself**. The web app had none either. This audit added `src/check_url_test.py` (19 tests, §4) so the CLI's behaviour is now pinned and guarded.

---

## 3. Performance: Profiling and Optimization

### 3.1 Where the ~20 s went (measured with `-X importtime` + component timing)

| Cost | Cause | Fixable? |
|---|---|---|
| ~14 s | Importing scikit-learn (triggered by unpickling any `.pkl` pipeline) | No — inherent to loading any sklearn pickle |
| ~5–10 s | Unpickling the 53 MB RandomForest (200 trees) | No — inherent to the artifact |
| **5.6 s** | Occlusion explanation ran **20 separate `predict_proba` calls** (1 base + 18 occluded rows + 1 benign baseline) | **Yes** |
| **1.4 s** | Importing pandas — used only to build a single 1×18 feature row | **Yes** |
| ~0.7 s | joblib spawning parallel workers per `predict_proba` call | Partially absorbed by batching |
| ~1.3 s | numpy/joblib base imports | No (irreducible) |

### 3.2 Optimization 1: batch the occlusion explanation (biggest win)
**What:** All 19 counterfactual rows (base + 18 single-feature occlusions + benign baseline) are now assembled into one matrix and scored in a **single `predict_proba` call**.

**Why this is safe:** Occlusion explanations are independent per-feature counterfactuals — scoring them in a batch produces mathematically identical results to scoring them one at a time (verified: zero numeric change in outputs, §4). Batching also amortizes joblib's per-call worker-spawn overhead.

**Result:** Explanation step 5.6 s → **0.36 s (~15×)**.

### 3.3 Optimization 2: drop pandas from the inference path
**What:** The single feature row is now built with plain numpy.

**Why:** pandas cost 1.4 s of import time for no benefit — the model consumes a numpy array either way. pandas remains a dependency for the *training/evaluation* scripts, where it earns its keep.

### 3.4 Optimization 3: `--fast` flag (the ~30× win)
**What:** `check_url.py <url> --fast` runs pure-Python LogisticRegression inference from a 2 KB `models/lr_fast.json` (weights, bias, scaler mean/std — all exported from the trained pipeline). It never imports sklearn, numpy, or joblib at all.

**Why LR and not RF?**
- LR inference is exact arithmetic: `z = bias + Σ wᵢ·(xᵢ−μᵢ)/σᵢ`, then sigmoid. A 200-tree forest cannot be reduced to arithmetic without shipping the whole forest.
- RF stays the default because it is the more accurate model (F1 0.8878 vs 0.8043). `--fast` is opt-in for interactive use where ~20 s latency is unusable — same trade-off a production email gateway would face (accuracy vs latency), made explicit rather than hidden.

**Why it's trustworthy:**
- The regression suite asserts `--fast` probabilities match the sklearn LR pipeline **to 6 decimal places** on every test URL (the same 1e-6 parity earlier proven for the browser export).
- **Freshness contract:** the test suite checks whether `lr_fast.json` is older than the trained `LogisticRegression.pkl`; if so it re-exports automatically. A stale export can never silently disagree with the model it claims to represent — this was the main risk of adding a second representation of the model.

**Why the export script changed too:** `src/export_model.py` previously wrote only to the web app dir (and unpickled the 53 MB RF even when only LR was needed). It now writes `models/lr_fast.json` first (cheap), and the web/RF exports are best-effort so regeneration of the fast model never depends on the web app directory existing.

### 3.5 Results

| Mode | End-to-end time | Notes |
|---|---|---|
| Before | ~20 s | dominated by sklearn import + 53 MB unpickle |
| After (RF, default) | ~20 s | floor is now entirely the unavoidable model load; explanation portion cut 15× |
| After (`--fast`) | **~0.65 s** | pure python, no sklearn/numpy/joblib imports |

---

## 4. Verification: Proving Nothing Broke

The refactor followed test-driven discipline. Because `check_url.py` had no tests, the **first** step was capturing a **golden master**: the exact `--json` output for 8 representative URLs from the *pre-optimization* code. That file (`src/check_url_golden.json`) then acted as the safety net.

`src/check_url_test.py` (19 tests) verifies:

1. **Golden master (8 tests):** replay each pinned URL through the real `main()` flow and require the full JSON — verdict, probability, all 18 features, per-feature occlusion contributions, benign baseline — to match to the last decimal.
2. **Batching contract (1 test):** the occlusion explanation must issue exactly **one** `predict_proba` call per URL. (Written first in RED form: it failed against the old code, which made 20 calls — proving the inefficiency was real before fixing it.)
3. **`--fast` parity (9 tests):** fast-mode verdict and probability must match the sklearn LR pipeline to 6 decimals on every test URL, and the freshness contract must hold.
4. Plus the full pre-existing suite: `features_test.py` **81/81** still green after all changes, and the web app typecheck + build stayed clean after the export refresh.

**Golden diff after the fix:** the only changed fields were the 13 `direction` labels on exact-zero contributions (bug fix §2.1). Every numeric value identical. That is the definition of a behaviour-preserving optimization.

---

## 5. Design Decisions and Why (consolidated)

Decisions made *before* this audit, verified as sound during it, are included so the rationale lives in one place:

| Decision | Why |
|---|---|
| **Lexical features only, no network calls** | Offline inference, low latency, no privacy/legal issues from visiting URLs, no dependency on blocklist availability. Documented cost: clean-looking phishing can evade detection. |
| **Exclude domain-age (WHOIS) feature** | Requires network access — breaks the offline-only guarantee (also in `evaluation_summary.md`). |
| **One self-contained sklearn Pipeline per model** (`StandardScaler` *inside* the LR pipeline) | Prevents scaler train/inference skew and CV leakage; each `.pkl` loads as one unit with no separate scaler file to mismatch. |
| **Train on real URL strings through the same `features.py` used at inference** | Guarantees train/inference feature parity by construction — the #1 source of silent ML bugs. |
| **Dataset: PhishTank + Tranco + ealvaradob benign (107,355 URLs)** | Tranco alone is bare homepages only (0% with paths) vs ~61% of PhishTank URLs having paths — the model would learn "path = phishing" (dataset bias, not signal). The ealvaradob benign subset (mostly deep links) fixes the class skew in path presence (61% phish / 77% legit have paths). |
| **Per-host cap (max 10 URLs/host)** | PhishTank had 5,700+ URLs on `docs.google.com` alone; uncapped, the model memorizes host patterns instead of transferable lexical signals. Capping removes a source artifact that inflates test metrics while hurting real-world generalization. |
| **Dedupe within class and across class (benign wins)** | Zero duplicates and zero train/test leakage by URL. |
| **`class_weight='balanced'`** | Missed phishing (FN) costs far more than false alarms (FP) in a security tool — favour recall; also handles the 45/55 class split. |
| **RF default, LR available, `--fast` opt-in** | RF is more accurate (F1 0.8878 vs 0.8043) but heavy to load; `--fast` gives sub-second interactive checks with LR, with parity tests guaranteeing agreement. The trade-off is explicit, not hidden. |
| **Batched occlusion (one `predict_proba`)** | Mathematically identical to per-row calls (independent counterfactuals), ~15× faster, and now *contractually pinned by a test* so it can't regress. |
| **numpy instead of pandas in the inference path** | pandas cost 1.4 s import for zero benefit at inference; it stays for training/evaluation where it's useful. |
| **`direction` from rounded contributions** | RF float noise (1e-16) must never leak into user-visible output determinism; rounding is already applied to the reported value, so labelling from the same value is consistent by construction. |
| **Warnings silenced in the CLI** | The CLI is meant to be embedded in scripts; stderr must carry only real errors. Matches the existing `train.py`/`evaluate.py` convention. |
| **Golden-master tests instead of asserting on internals** | Pin observable behaviour, not implementation — the suite survives refactors and would catch any future output drift, including accidental retraining effects. |
| **Freshness contract for `lr_fast.json`** | A second representation of a model is a drift risk by definition; auto-regeneration on staleness makes the failure mode impossible rather than merely unlikely. |
| **Web export quarantined + best-effort** | The deliverable is the model + CLI; the web demo must never break training if `workspace/` is deleted, but its exported model must never drift from the trained pipeline (export runs automatically at the end of `train`, reads metrics live from `training_report.json`, nothing hard-coded). |
| **Earlier honest-metrics reset** | An earlier run on a tiny 244-URL dataset reported F1 = 1.000 — a class-separability artifact (trivially separable by TLD), not quality. Reported numbers come only from the 107k-URL dataset. |

---

## 6. Residual Limitations (unchanged, documented for honesty)

1. ~20 s remains in default RF mode — the floor is sklearn import + 53 MB unpickle. Only alternatives are `--fast` (shipped), a lighter forest (accuracy cost), or ONNX/native inference (out of scope for this project).
2. Lexical-only detection cannot catch clean-looking phishing (mitigated by documented recall-first threshold guidance, §Ethical Considerations in README).
3. PhishTank/Tranco/ealvaradob source skew (hosted campaign phishing; popular-site legit) is mitigated, not eliminated.
4. `site.com.au`-style ambiguity persists without a Public Suffix List.

---

## 7. Reproducing This Audit

```bash
cd phishing-detector
.venv/bin/python src/features_test.py                          # 81/81
.venv/bin/python src/check_url_test.py                         # 19/19 (loads both models; ~1 min)
.venv/bin/python src/check_url.py <url> --fast                 # ~0.65 s
.venv/bin/python src/check_url.py <url> --fast --json          # machine-readable
cd ../workspace && npm run typecheck && npm run build          # web app
```
