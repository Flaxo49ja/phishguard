# Phishing URL Detector

> This folder is the training pipeline for the PhishGuard site in `../web/`.

A Python CLI tool that classifies URLs as phishing or legitimate using lexical and structural features — **no network calls, no visiting URLs**.

```
python check_url.py <url>
```

> Full pipeline (per-model sklearn Pipelines, self-contained `.pkl` files, 107k real-URL dataset) — see Metrics below.
>
> **Audit & optimization report:** `reports/audit_and_optimization_report.md` — everything that was tested, every bug found and fixed (nondeterministic output, warning spam, ~20 s startup), the full profiling breakdown, the `--fast` design, and the reasoning behind every design decision.

---

## Problem Statement

Phishing attacks remain one of the most common and effective cyberattack vectors. Attackers create deceptive URLs that mimic legitimate services (banks, email providers, payment platforms) to steal credentials, install malware, or trick users into transactions. Existing solutions often rely on real-time DNS lookups, WHOIS queries, or blocklist APIs — which add latency, require network access, and may miss brand-new phishing URLs.

This tool takes a different approach: it extracts **purely lexical and structural features** from the URL string itself (length, hostname patterns, subdomain count, entropy, presence of IP addresses, known shorteners, TLD-in-subdomain patterns, etc.) and uses a trained machine learning model to classify it. Because no network calls are made, the tool works offline, has low latency, and can be embedded in email gateways, browser extensions, or CLI scripts.

---

## How to Run

### Setup

```bash
# 1. Clone/create the project
cd phishing-detector

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. (Optional) Download a dataset
#    UCI Phishing Websites Dataset (benchmark reference only):
python -m src.fetch_data

#    Build the real custom dataset (PhishTank + Tranco + ealvaradob benign):
python -m src.fetch_data --custom
#    (requires data/raw/phishtank.csv, tranco_top10k.csv and ealvaradob_urls.json)
```

### Train a Model

```bash
# Train on the custom dataset (default)
python -m src.train --source custom

# Or train on UCI dataset
python -m src.train --source uci
```

This will:
- Split data 80/20 (stratified)
- Build one **sklearn Pipeline per model** — LogisticRegression gets `StandardScaler` inside its pipeline; RandomForest runs unscaled (trees don't need scaling)
- Train both with `class_weight='balanced'`
- Run 5-fold cross-validation (CV refits the whole pipeline per fold — no scaler leakage)
- Refresh the optional web-app export (`src/export_model.py`, best-effort) so it always matches the models just trained
- Save each fitted pipeline as a single self-contained `.pkl` in `models/` (no separate scaler)
- Save feature importances and reports to `reports/`

### Evaluate

```bash
python -m src.evaluate --source custom
```

This generates:
- `reports/metrics.json` — raw precision/recall/F1/ROC-AUC/confusion matrix
- `reports/confusion_matrix.png` — heatmap visualization
- `reports/roc_curve.png` — ROC curve
- `reports/evaluation_summary.md` — markdown summary with ethical analysis

### Check a URL

```bash
# Human-readable output
python src/check_url.py https://www.google.com

# Machine-readable JSON output
python src/check_url.py https://paypal.com.verify-login.ru/secure/auth --json

# Check a URL without a scheme (auto-prepend http://)
python src/check_url.py bit.ly/3xample

# List available trained models
python src/check_url.py --list-models

# Use a specific model
python src/check_url.py <url> --model LogisticRegression

# Fast startup: pure-python LogisticRegression from models/lr_fast.json
# (~0.6 s total instead of ~20 s; same verdicts, probabilities match the
#  sklearn LR pipeline to 6 decimal places — guarded by check_url_test.py)
python src/check_url.py <url> --fast
```

**Output format (human-readable):**
```
URL: https://www.google.com
Verdict: LEGITIMATE
Phishing probability: 0.1250

Top contributing features:
  - num_hyphens: 0
  - num_subdomains: 1
  - num_dots: 2
  - num_slashes: 2
  - hostname_length: 14
```

**Output format (JSON):**
```json
{
  "url": "https://www.google.com",
  "verdict": "LEGITIMATE",
  "phishing_probability": 0.125,
  "threshold": 0.5,
  "features": { ... },
  "top_contributing_features": [ ... ]
}
```

---

## Features Extracted (18 total)

All features are pure string/URL parsing — **no `requests`, no WHOIS, no network calls**.

| # | Feature | Description |
|---|---------|-------------|
| 1 | `url_length` | Total character length of the URL |
| 2 | `hostname_length` | Length of the hostname portion |
| 3 | `path_length` | Length of the URL path |
| 4 | `num_dots` | Count of `.` characters |
| 5 | `num_hyphens` | Count of `-` characters |
| 6 | `num_underscores` | Count of `_` characters |
| 7 | `num_slashes` | Count of `/` characters |
| 8 | `num_digits` | Count of digit characters (0-9) |
| 9 | `num_special_chars` | Count of `@ % = & ? # + $ ,` |
| 10 | `has_at_symbol` | 1 if `@` present (credential injection) |
| 11 | `has_ip_address` | 1 if hostname is a raw IPv4 address |
| 12 | `num_subdomains` | Number of subdomain segments |
| 13 | `uses_https` | 1 if scheme is https |
| 14 | `has_https_token_in_path` | 1 if "https" appears in the path |
| 15 | `is_shortened_url` | 1 if hostname matches known shorteners |
| 16 | `url_entropy` | Shannon entropy of URL string |
| 17 | `tld_in_subdomain` | 1 if TLD appears as subdomain (e.g. `paypal.com.verify-login.ru`); exempted for ccTLD second-level domains so `bbc.co.uk` does not falsely fire on the `co` segment |
| 18 | `digit_letter_ratio` | Ratio of digits to letters |

### Deliberately Excluded

- **Domain age (WHOIS)**: Requires network access, breaks the offline-only guarantee. Would be a valuable addition for a production system but is excluded here for latency and offline requirements.

---

## Dataset

### Primary: PhishTank + Tranco + ealvaradob (107,355 real URLs)

The delivered model trains on **real URL strings** through the exact same `features.py` pipeline used at inference (train/inference parity guaranteed).

| Source | Class | Rows | Notes |
|--------|-------|------|-------|
| PhishTank verified feed (`online-valid.csv`) | phishing | 48,338 | after dedupe + per-host cap |
| Tranco top-10k (`tranco-list.eu`) | legitimate | — | bare homepages (top domains) |
| ealvaradob/phishing-dataset benign subset (Hugging Face) | legitimate | — | real deep links **with paths** |
| **Total** | | **107,355** | 48,338 phish / 59,017 legit |

- **Why ealvaradob benign?** Tranco contains ONLY bare domains (0% with paths) while ~61% of PhishTank URLs have paths. Training on Tranco alone teaches the model "any path = phishing" — dataset bias, not signal. The ealvaradob benign subset (444,933 real benign URLs, mostly deep links) fixes this: both classes now contain plenty of URLs with paths (61% phish / 77% legit).
- **Why per-host capping (max 10 URLs/host)?** PhishTank had 5,700+ URLs on `docs.google.com` alone — without capping, the model memorizes host-level patterns ("3 dots + short host = phishing", i.e. the Google Forms pattern) instead of learning transferable lexical signals. Host capping is a generalization safeguard: it removes a source-level artifact that would inflate metrics while hurting real-world performance on unseen hosts.
- **Dedupe**: exact-URL dedupe per class + cross-class dedupe (benign label wins). Zero duplicates, zero train/test leakage by URL.
- **Usage**: place `phishtank.csv`, `tranco_top10k.csv` and `ealvaradob_urls.json` in `data/raw/`, then:
  ```bash
  python -m src.fetch_data --custom
  ```
  This produces `data/processed/custom_dataset.csv` with columns `url, label`.

> **Scope note:** the deliverable is the trained model + CLI. A sibling web demo (`../web/`, PhishGuard) exists as an optional extra; `src/export_model.py` feeds it but is quarantined — it runs automatically at the end of `python -m src.train` (best-effort, never fatal) so its exported JSON can never silently drift from the trained pipeline, and all metrics in the export are read live from `reports/training_report.json` at export time (nothing hard-coded). Delete `src/export_model.py` and `../web/` to drop the web integration entirely; nothing else in this project references them.

### Secondary benchmark: UCI Phishing Websites Dataset

- **Source**: UCI Machine Learning Repository (id=327)
- **URL**: https://archive.ics.uci.edu/dataset/327/phishing+websites
- **Contents**: ~11,055 rows with 30 pre-engineered (anonymized) features + binary label
- **Role**: benchmark reference only — **not wired into the training path**. Its features are pre-engineered and anonymized (no raw URL text), incompatible with `features.py`'s `extract_features(url)` used by `check_url.py`, and several of its features (`page_rank`, `web_traffic`, `google_index`, `dnsrecord`, `age_of_domain`) require network/WHOIS lookups that contradict the offline-only design. It confirms the problem is learnable at scale; cached at `data/raw/uci_phishing.csv` via `python -m src.fetch_data`.

---

## Metrics

### Latest Training Run (107,355 real URLs, 80/20 stratified split)

| Model | Precision | Recall | F1 | ROC-AUC | CV F1 (mean ± std) |
|-------|-----------|--------|-----|---------|---------------------|
| **RandomForest** | 0.8885 | 0.8872 | **0.8878** | 0.9545 | 0.8890 ± 0.0023 |
| LogisticRegression | 0.8124 | 0.7963 | 0.8043 | 0.8850 | 0.8015 ± 0.0033 |

- **Best model**: RandomForest (saved to `models/RandomForest.pkl` as a single fitted pipeline)
- **Test set**: 21,471 URLs (stratified: 9,668 legit + 11,803 phishing held out)
- **Confusion matrix (RandomForest)**: TN=10,727, FP=1,076, FN=1,091, TP=8,577
- These are realistic, honest numbers on real data — an earlier run on a tiny 244-URL dataset reported F1=1.000, which was a class-separability artifact (the classes were trivially distinguishable by TLD alone), not model quality.

### CLI Smoke Tests (delivered RandomForest pipeline)

| URL | Verdict | Phishing probability |
|-----|---------|----------------------|
| `https://google.com` | LEGITIMATE | 0.000 |
| `https://www.google.com` | LEGITIMATE | 0.160 |
| `https://github.com/python/cpython` | LEGITIMATE | 0.200 |
| `http://paypal.com.verify-login.ru/user/login` | PHISHING | 0.705 |
| `https://bit.ly/3xY2zAb` (shortlink) | PHISHING | 1.000 |

All 81 feature unit tests pass (`python src/features_test.py`), and 19 CLI regression tests pass (`python src/check_url_test.py`): a golden master pins the exact `--json` output (verdict, probability, all 18 features, occlusion contributions, benign baseline) for 8 URLs, the occlusion explanation must run as ONE batched predict_proba call (20 separate calls cost ~5.6 s and are now one ~0.4 s call), and `--fast` pure-python inference must match the sklearn LR pipeline to 6 decimal places.

### Feature Importances (RandomForest)

Top 5 features by mean decrease in impurity:

1. `hostname_length` — 17.5%
2. `path_length` — 17.4%
3. `url_entropy` — 14.1%
4. `num_subdomains` — 9.7%
5. `num_slashes` — 9.2%

Full ranking in `reports/RandomForest_feature_importances.csv` and chart at `reports/RandomForest_feature_importances.png`.

---

## Demo Video

```
[INSERT SCREENSHOT/GIF HERE]
```

Recommended demo:

1. Run on a known legitimate URL:
   ```bash
   python src/check_url.py https://www.google.com
   ```
2. Run on a known phishing URL:
   ```bash
   python src/check_url.py https://paypal.com.verify-login.ru/secure/auth
   ```
3. Show the `--json` flag for machine-readable output:
   ```bash
   python src/check_url.py <url> --json
   ```

Record your screen while running these commands. The demo should be under 60 seconds.

---

## Ethical Considerations

### The Precision/Recall Trade-off

In phishing detection, the two error types have very different costs:

| Error Type | Meaning | Cost |
|------------|---------|------|
| **False Positive** (FP) | Legitimate URL flagged as phishing | Inconvenience — user can't access a real site. In high-stakes contexts (banking portals, healthcare), this can be severe. |
| **False Negative** (FN) | Phishing URL classified as legitimate | Security risk — user may be tricked into entering credentials or downloading malware. This is the **more dangerous** error. |

### Our Approach

This project prioritizes **recall over precision** because missing a phishing URL is worse than a false alarm. We achieve this through:

1. **`class_weight='balanced'`** during training — the model is penalized more for misclassifying the minority (phishing) class.
2. **Stratified train/test splits** — ensures both classes are represented in evaluation.
3. **Threshold flexibility** — the `--threshold` flag in `check_url.py` allows lowering the decision threshold (e.g. to 0.3) for higher recall at the cost of more false positives.

### Current Class Balance

The training dataset has a phishing ratio of ~45% (48,338 phishing / 59,017 legitimate). In the real world, legitimate URLs vastly outnumber phishing ones. Our model is trained on a roughly balanced sample for demonstration purposes. For production use:

- You would train on a dataset that reflects real-world prevalence (e.g. 99.9% legitimate, 0.1% phishing).
- You would use `class_weight='balanced'` or SMOTE to ensure the model doesn't just learn to predict "legitimate" for everything.
- You would set a lower decision threshold (e.g. 0.3 instead of 0.5) to catch more phishing URLs.

### Limitations

1. **Lexical features only**: We don't visit URLs, check DNS, or query blocklists. Sophisticated phishing URLs that look lexically "clean" may evade detection.
2. **No domain age check**: WHOIS-based features (domain age, registration privacy) are strong phishing signals but require network access.
3. **Dataset skew**: PhishTank skews toward hosted/campaign phishing (Google Forms, weebly sites); Tranco+ealvaradob skew toward popular sites. Long-tail legitimate domains and novel phishing kits are underrepresented.
4. **Adversarial adaptation**: Phishers can evolve their tactics. Models need regular retraining.
5. **Language/cultural bias**: Our features are language-agnostic, but phishing tactics vary by region and target demographic.
6. **Inherent lexical ambiguity**: e.g. `site.com.au` looks like a TLD-in-subdomain pattern (`.site` is a real gTLD at the leftmost position) — indistinguishable from a homograph without a Public Suffix List.

### Responsible Use

- This tool is for **educational and defensive purposes**.
- Do not use it to make automated blocking decisions without human review.
- Always allow users to override a "phishing" verdict (false positives happen).
- Combine with other signals (reputation, blocklists, user reports) for defense-in-depth.

---

## Project Structure

```
phishing-detector/
├── data/
│   ├── raw/              # downloaded datasets (UCI, PhishTank, Tranco)
│   └── processed/        # cleaned CSVs with url+label
├── src/
│   ├── fetch_data.py     # downloads/loads datasets (UCI + custom pipeline)
│   ├── features.py       # 18 feature extraction functions
│   ├── features_test.py  # unit tests on known URLs
│   ├── train.py          # trains RF + LR pipelines, saves both + web export
│   ├── evaluate.py       # precision/recall/F1, confusion matrix, ROC
│   ├── export_model.py   # OPTIONAL web-app JSON export (quarantined)
│   ├── check_url.py      # CLI for checking individual URLs
│   ├── check_url_test.py # regression tests: golden-master CLI outputs, batched occlusion, --fast parity
│   └── check_url_golden.json # pinned expected CLI JSON outputs (8 URLs)
├── models/               # one self-contained pipeline .pkl per model + lr_fast.json (pure-python --fast model)
├── reports/              # metrics.json, confusion_matrix.png, etc.
├── requirements.txt
└── README.md
```

---

## Requirements

- Python 3.11+
- scikit-learn >= 1.3.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- ucimlrepo (optional — only for the UCI benchmark download)

See `requirements.txt` for pinned versions.

---

## License

BSD 3-Clause License. See LICENSE file (if included).
