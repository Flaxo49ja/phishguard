"""
export_model.py - Export the trained model(s) to JSON for the PhishGuard web app.

STATUS: OPTIONAL / QUARANTINED. The PhishGuard web app is a sibling demo
(../web/) that is OUT OF SCOPE for the deliverable (trained model + CLI).
This module is kept only so the demo does not silently go stale:

- It is invoked automatically at the end of `python -m src.train`, so the
  exported JSON can never drift from the just-trained models.
- Its metrics are read dynamically from reports/training_report.json at
  export time (nothing is baked in).
- To remove the web integration entirely, delete this file and ../web/ —
  nothing else in this project references them.

LogisticRegression pipelines are fully exportable: the StandardScaler step is
just (x - mean) / scale and the LR step is sigmoid(bias + sum(w_i * x_i_std)),
so ~2 KB of JSON reproduces inference exactly. RandomForest can't be exported
losslessly, so we export its global feature importances for UI display.

Usage:
    python src/export_model.py   (also runs automatically after training)
Writes:
    web/src/model/lrModel.json          (full pipeline, browser inference)
    web/src/model/rfFeatureImportances.json (UI display data)
"""

import json
from pathlib import Path

import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
WEB_SRC = BASE_DIR.parent / "web" / "src"

try:
    from features import get_feature_names
except ImportError:
    from .features import get_feature_names

REPORT_PATH = BASE_DIR / "reports" / "training_report.json"
DATASET_LABEL = "PhishTank + Tranco + ealvaradob benign"


def _r(value, nd: int = 4):
    """Round for JSON export; None-safe so missing metrics stay null."""
    return None if value is None else round(float(value), nd)


def _training_metrics() -> dict:
    """Pull live metrics from reports/training_report.json (written by train.py).

    Metrics are NEVER baked in here — if the report is missing, export with
    nulls rather than stale hard-coded values. The web app consumes this blob
    verbatim (web/src/modelLoader.ts -> REAL_METRICS), so numbers stay
    in sync automatically across retrains.
    """
    try:
        report = json.loads(REPORT_PATH.read_text())
    except (OSError, ValueError) as exc:
        print(f"[export_model] WARNING: could not read {REPORT_PATH} ({exc}) — metrics will be null")
        return {}

    cmp_ = report.get("comparison", {})

    def model_metrics(name: str) -> dict:
        mm = cmp_.get(name, {})
        out = {
            "precision": _r(mm.get("precision")),
            "recall": _r(mm.get("recall")),
            "f1": _r(mm.get("f1")),
            "rocAuc": _r(mm.get("roc_auc")),
        }
        if mm.get("cv_f1_mean") is not None:
            out["cvF1"] = f"{mm['cv_f1_mean']:.4f} ± {mm['cv_f1_std']:.4f}"
        cm = mm.get("confusion_matrix")
        if cm and len(cm) == 2 and len(cm[0]) == 2:  # sklearn order: [[TN, FP], [FN, TP]]
            out["confusion"] = {"tn": cm[0][0], "fp": cm[0][1], "fn": cm[1][0], "tp": cm[1][1]}
        return out

    return {
        "datasetLabel": DATASET_LABEL,
        "nSamples": report.get("n_samples"),
        "nPhishing": report.get("n_phishing"),
        "nLegitimate": report.get("n_legitimate"),
        "testSetSize": report.get("test_size"),
        "logisticRegression": model_metrics("LogisticRegression"),
        "randomForest": model_metrics("RandomForest"),
    }


def _warn_if_stale(force: bool) -> None:
    """Surface drift: is the previous export older than the current .pkl files?"""
    out_lr = WEB_SRC / "model" / "lrModel.json"
    if not out_lr.exists() or force:
        return
    pkl_times = [p.stat().st_mtime for p in MODELS_DIR.glob("*.pkl")]
    if pkl_times and out_lr.stat().st_mtime < max(pkl_times):
        print(
            "[export_model] WARNING: previous export was STALE (older than models/*.pkl) "
            "— refreshing now. This is why the export also runs automatically after training."
        )


def export(force: bool = False, include_rf: bool = True):
    _warn_if_stale(force)
    m = _training_metrics()
    feature_names = get_feature_names()

    # ---- LogisticRegression: exact export ---------------------------------
    lr_path = MODELS_DIR / "LogisticRegression.pkl"
    if not lr_path.exists():
        raise FileNotFoundError(f"{lr_path} not found — train first: python -m src.train")
    pipeline = joblib.load(lr_path)

    scaler = pipeline.named_steps["scaler"]
    clf = pipeline.named_steps["clf"]

    # classes_ is [0, 1]; coef_[0] maps features -> log-odds of class 1 (phishing)
    assert list(clf.classes_) == [0, 1], f"Unexpected classes: {clf.classes_}"

    model = {
        "kind": "LogisticRegression",
        "featureNames": feature_names,
        "scaler": {
            "means": [round(float(m), 8) for m in scaler.mean_],
            "stds": [round(float(s), 8) for s in scaler.scale_],
        },
        "weights": [round(float(w), 8) for w in clf.coef_[0]],
        "bias": round(float(clf.intercept_[0]), 8),
        "threshold": 0.5,
        "metrics": m or None,
        "meta": {
            "source": "metrics come from reports/training_report.json (read at export time — never baked in)",
            "trainedOn": "real URLs (PhishTank + Tranco + ealvaradob benign) — see metrics block",
            "exportedAt": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        },
    }

    # ---- fast CLI model (pure-python inference for check_url.py --fast) ----
    # Written FIRST and always: the CLI fast path depends on it, the web app
    # does not. Slim copy (weights only, no metrics blob) — ~2 KB on disk.
    fast_model = {
        "kind": "LogisticRegressionFast",
        "featureNames": feature_names,
        "scaler": model["scaler"],
        "weights": model["weights"],
        "bias": model["bias"],
        "threshold": model["threshold"],
    }
    fast_path = MODELS_DIR / "lr_fast.json"
    fast_path.write_text(json.dumps(fast_model, indent=2))
    print(f"[export_model] fast CLI model -> {fast_path}")

    # ---- optional web-app export (best-effort: web/ may be absent) ---
    try:
        out_lr = WEB_SRC / "model" / "lrModel.json"
        out_lr.parent.mkdir(parents=True, exist_ok=True)
        out_lr.write_text(json.dumps(model, indent=2))
        print(f"[export_model] LR pipeline -> {out_lr}")
    except OSError as exc:
        print(f"[export_model] NOTE: web-app export skipped (non-fatal): {exc}")

    # ---- RandomForest: importances only ------------------------------------
    rf_path = MODELS_DIR / "RandomForest.pkl"
    if include_rf and rf_path.exists():
        rf = joblib.load(rf_path)
        rf_clf = rf.named_steps["clf"]
        importances = {
            name: round(float(imp), 6)
            for name, imp in sorted(
                zip(feature_names, rf_clf.feature_importances_),
                key=lambda kv: kv[1],
                reverse=True,
            )
        }
        rf_out = {
            "kind": "RandomForest",
            "note": (
                "Global feature importances only. A 200-tree forest cannot be exported "
                "to JSON losslessly; authoritative predictions come from the Python CLI "
                "(python src/check_url.py <url>)."
            ),
            "testF1": (m.get("randomForest") or {}).get("f1"),
            "testRocAuc": (m.get("randomForest") or {}).get("rocAuc"),
            "importances": importances,
        }
        out_rf = WEB_SRC / "model" / "rfFeatureImportances.json"
        try:
            out_rf.write_text(json.dumps(rf_out, indent=2))
            print(f"[export_model] RF importances -> {out_rf}")
        except OSError as exc:
            print(f"[export_model] NOTE: web-app RF export skipped (non-fatal): {exc}")


if __name__ == "__main__":
    export()
