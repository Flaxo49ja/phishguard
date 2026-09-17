"""
evaluate.py - Evaluate a trained model and generate reports.

- Load the trained pipeline from models/ (scaler — when present — is
  embedded inside the pipeline; no separate scaler.pkl)
- Compute precision, recall, F1, ROC-AUC, confusion matrix
- Save confusion matrix as PNG (matplotlib + seaborn)
- Save metrics.json with all numbers
- Generate a markdown summary of the precision/recall trade-off
"""

import json
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

try:  # package mode (python -m src.evaluate) or script mode (python src/evaluate.py)
    from .features import extract_features, get_feature_names
except ImportError:
    from features import extract_features, get_feature_names

# Default model name (matches what train.py saves)
DEFAULT_MODEL_NAME = "RandomForest"


def _ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(
    model_path: Optional[Path] = None,
    data_source: str = "custom",
    model_name: str = DEFAULT_MODEL_NAME,
) -> Dict[str, Any]:
    """
    Load the trained pipeline, evaluate on test data, save reports.

    Returns the full metrics dict.
    """
    _ensure_dirs()

    model_path = model_path or MODELS_DIR / f"{model_name}.pkl"

    print(f"[evaluate] Loading pipeline from: {model_path}")

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}. Run train.py first.")

    model = joblib.load(model_path)

    # Load data
    from train import load_training_data, build_feature_matrix

    print(f"[evaluate] Loading data from: {data_source}")
    df = load_training_data(data_source)

    print(f"[evaluate] Dataset: {len(df)} URLs "
          f"({df['label'].sum()} phishing, {(1 - df['label']).sum()} legit)")

    # Stratified 80/20 split (same as training for fair eval)
    from sklearn.model_selection import train_test_split

    X = build_feature_matrix(df["url"])
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Predict (any scaling happens inside the pipeline)
    y_pred = model.predict(X_test)
    y_prob = None
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]

    # Compute metrics
    metrics: Dict[str, Any] = {
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_test, y_prob))
        except ValueError:
            metrics["roc_auc"] = None

    print(f"\n[evaluate] Results:")
    print(f"  Precision : {metrics['precision']:.4f}")
    print(f"  Recall    : {metrics['recall']:.4f}")
    print(f"  F1        : {metrics['f1']:.4f}")
    if metrics.get("roc_auc") is not None:
        print(f"  ROC-AUC   : {metrics['roc_auc']:.4f}")
    tn, fp, fn, tp = metrics["confusion_matrix"][0][0], metrics["confusion_matrix"][0][1], \
                     metrics["confusion_matrix"][1][0], metrics["confusion_matrix"][1][1]
    print(f"  Confusion : TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    # Save confusion matrix PNG
    save_confusion_matrix_png(
        y_test, y_pred,
        REPORTS_DIR / "confusion_matrix.png",
        model_name,
    )

    # Save ROC curve
    if y_prob is not None:
        save_roc_curve_png(
            y_test, y_prob,
            REPORTS_DIR / "roc_curve.png",
            model_name,
        )

    # Save metrics.json
    save_metrics_json(metrics, model_name)

    # Save markdown summary
    save_markdown_summary(metrics, model_name, df)

    return metrics


def save_confusion_matrix_png(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    path: Path,
    model_name: str,
):
    """Save a labeled confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)
    labels = ["Legitimate (0)", "Phishing (1)"]

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=labels, yticklabels=labels,
        cbar_kws={"label": "Count"},
        ax=ax,
    )
    ax.set_title(f"Confusion Matrix — {model_name}")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    plt.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"[evaluate] Confusion matrix saved to {path}")


def save_roc_curve_png(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    path: Path,
    model_name: str,
):
    """Save an ROC curve plot."""
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    auc = roc_auc_score(y_true, y_prob)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, label=f"{model_name} (AUC = {auc:.4f})", linewidth=2)
    ax.plot([0, 1], [0, 1], "k--", label="Random guess", linewidth=1)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC Curve — {model_name}")
    ax.legend(loc="lower right")
    plt.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"[evaluate] ROC curve saved to {path}")


def save_metrics_json(metrics: Dict[str, Any], model_name: str):
    """Save metrics to reports/metrics.json."""
    path = REPORTS_DIR / "metrics.json"

    # Load existing if present
    if path.exists():
        with open(path) as f:
            existing = json.load(f)
    else:
        existing = {}

    existing[model_name] = metrics

    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"[evaluate] Metrics saved to {path}")


def save_markdown_summary(
    metrics: Dict[str, Any],
    model_name: str,
    df: pd.DataFrame,
):
    """Save a markdown summary of results for the README/report."""
    tn, fp, fn, tp = metrics["confusion_matrix"][0][0], metrics["confusion_matrix"][0][1], \
                     metrics["confusion_matrix"][1][0], metrics["confusion_matrix"][1][1]

    n_phishing = int(df["label"].sum())
    n_legit = int((1 - df["label"]).sum())

    summary = f"""# Evaluation Summary — {model_name}

## Dataset

- Total URLs: {len(df)}
- Phishing (positive): {n_phishing} ({n_phishing / len(df) * 100:.1f}%)
- Legitimate (negative): {n_legit} ({n_legit / len(df) * 100:.1f}%)
- Class imbalance ratio (phish/total): {df["label"].mean():.3f}

## Metrics

| Metric       | Value   |
|--------------|---------|
| Precision    | {metrics["precision"]:.4f} |
| Recall       | {metrics["recall"]:.4f} |
| F1 Score     | {metrics["f1"]:.4f} |
| ROC-AUC      | {metrics.get("roc_auc", "N/A")} |
| Model        | {model_name} |

## Confusion Matrix

|                     | Predicted Legit | Predicted Phish |
|---------------------|-----------------|-----------------|
| **Actual Legit**    | {tn} (TN)       | {fp} (FP)       |
| **Actual Phish**    | {fn} (FN)       | {tp} (TP)       |

## Precision/Recall Trade-off — Ethical Considerations

- **False Positives (FP = {fp}):** Legitimate URLs flagged as phishing.
  Cost: *inconvenience* — a real site is blocked, users may lose trust
  or be unable to access a service. In high-stakes contexts (e.g. banking,
  healthcare portals) this can be severe.

- **False Negatives (FN = {fn}):** Phishing URLs classified as legitimate.
  Cost: *security risk* — a user may be tricked into entering credentials
  or downloading malware. This is the more dangerous error type.

- **Recall = {metrics["recall"]:.4f}** means we catch {metrics["recall"]*100:.1f}% of phishing URLs.
  With {fn} missed phishing URLs out of {n_phishing} total, each miss
  represents a potential victim.

- **Precision = {metrics["precision"]:.4f}** means when we flag a URL as phishing,
  we are correct {metrics["precision"]*100:.1f}% of the time. The remaining
  {fp} false positives are a nuisance but far less costly than a miss.

- **Class imbalance** was handled with `class_weight="balanced"` during
  training. The dataset has a phishing ratio of {df["label"].mean():.3f},
  so the model is explicitly penalized for ignoring the minority (phishing) class.

### Recommendation

For a security tool where missing a phishing URL is worse than a false alarm,
we should *favor recall over precision*. This can be done by lowering the
decision threshold below 0.5, but that would increase false positives.

The current F1 = {metrics["f1"]:.4f} balances both concerns. For a production
deployment, consider:

1. A higher-recall operating point (threshold ~0.3–0.4) if the cost of a
   missed phishing URL is high (e.g. enterprise email gateway).
2. A human-in-the-loop review for URLs with probability 0.3–0.7, where the
   model is uncertain.
3. Regular retraining as phishing tactics evolve.

## Excluded Features

{docstring_for_excluded_features()}
"""
    path = REPORTS_DIR / "evaluation_summary.md"
    with open(path, "w") as f:
        f.write(summary)
    print(f"[evaluate] Markdown summary saved to {path}")


def docstring_for_excluded_features() -> str:
    from features import _DOMAIN_AGE_NOTE
    return f"- **{ _DOMAIN_AGE_NOTE}**"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate trained phishing detector model")
    parser.add_argument(
        "--source",
        choices=["uci", "custom"],
        default="custom",
        help="Dataset source (default: custom)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_NAME,
        help=f"Model name to evaluate (default: {DEFAULT_MODEL_NAME})",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PHISHING DETECTOR — EVALUATION")
    print("=" * 60)

    try:
        metrics = evaluate(
            data_source=args.source,
            model_name=args.model,
        )
        print("\n" + "=" * 60)
        print("EVALUATION COMPLETE")
        print("=" * 60)
        print(f"  F1 = {metrics['f1']:.4f}")
        print(f"  Precision = {metrics['precision']:.4f}")
        print(f"  Recall = {metrics['recall']:.4f}")
    except FileNotFoundError as exc:
        print(f"\nError: {exc}")
        raise SystemExit(1)
