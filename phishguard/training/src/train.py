"""
train.py - Train RandomForest and LogisticRegression models.

- 80/20 stratified train/test split (on unscaled features)
- One sklearn.Pipeline per model:
    * LogisticRegression: StandardScaler -> LogisticRegression (scaler fits
      inside the pipeline / inside each CV fold — no leakage)
    * RandomForest: classifier only (trees don't need scaling)
- 5-fold cross-validation (mean +/- std F1)
- Compare RF vs LogisticRegression on precision, recall, F1, ROC-AUC
- Save each fitted pipeline as a single .pkl to models/
- Save both models' metrics + feature importances to reports/
- Handle class imbalance via class_weight='balanced'
"""

import json
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:  # package mode (python -m src.train) or script mode (python src/train.py)
    from .features import extract_features, get_feature_names, _DOMAIN_AGE_NOTE
except ImportError:
    from features import extract_features, get_feature_names, _DOMAIN_AGE_NOTE

try:  # optional web-app export (out-of-scope sibling demo); train.py must not fail without it
    from .export_model import export as _export_web_model
except ImportError:
    try:
        from export_model import export as _export_web_model
    except ImportError:
        _export_web_model = None

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"


def _ensure_dirs():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_training_data(source: str = "custom") -> pd.DataFrame:
    """
    Load a labeled URL dataset for training.

    If source == "custom", expects data/processed/custom_dataset.csv
    with columns ['url', 'label'].

    If source == "uci", expects data/raw/uci_phishing.csv with a 'label'
    column (and feature columns already present — we'll extract fresh
    features from the URL string instead).
    """
    if source == "custom":
        path = DATA_PROCESSED / "custom_dataset.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run: python -m src.fetch_data --custom"
            )
        df = pd.read_csv(path)
        if "url" not in df.columns or "label" not in df.columns:
            raise KeyError(
                f"Expected columns ['url', 'label'] in {path}. "
                f"Got: {list(df.columns)}"
            )
        return df[["url", "label"]]

    elif source == "uci":
        path = PROJECT_ROOT / "data" / "raw" / "uci_phishing.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run: python -m src.fetch_data"
            )
        df = pd.read_csv(path)
        if "url" not in df.columns:
            raise KeyError(f"No 'url' column in {path}")
        if "label" not in df.columns:
            raise KeyError(f"No 'label' column in {path}")
        return df[["url", "label"]]

    else:
        raise ValueError(f"Unknown source: {source}")


def build_feature_matrix(urls: pd.Series) -> np.ndarray:
    """Extract features from a Series of URL strings -> (n_samples, n_features) array."""
    feature_list = [extract_features(u) for u in urls]
    df = pd.DataFrame(feature_list, columns=get_feature_names())
    return df.values.astype(np.float64)


# ---------------------------------------------------------------------------
# Training + evaluation helpers
# ---------------------------------------------------------------------------

Metrics = Dict[str, Any]


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
) -> Metrics:
    """Compute precision, recall, F1, ROC-AUC, confusion matrix."""
    metrics: Metrics = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except ValueError:
            metrics["roc_auc"] = None
    return metrics


def train_and_evaluate(
    pipeline: Any,
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    model_name: str,
    feature_names: list,
) -> Tuple[Any, Metrics, Optional[np.ndarray]]:
    """
    Fit a full Pipeline on the training set, evaluate on the test set,
    and run 5-fold CV (CV re-fits the whole pipeline per fold, so the
    scaler — when present — is fit inside each fold with no leakage).

    Returns: (fitted_pipeline, test_metrics, feature_importances_or_None)
    """
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = None
    if hasattr(pipeline, "predict_proba"):
        y_prob = pipeline.predict_proba(X_test)[:, 1]

    test_metrics = compute_metrics(y_test, y_pred, y_prob)

    # 5-fold CV on training set
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1")
    test_metrics["cv_f1_mean"] = float(cv_scores.mean())
    test_metrics["cv_f1_std"] = float(cv_scores.std())

    # Feature importances live on the classifier step (only for RF)
    importances = None
    clf = pipeline.named_steps.get("clf")
    if clf is not None and hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_

    print(f"\n--- {model_name} ---")
    print(f"  Precision : {test_metrics['precision']:.4f}")
    print(f"  Recall    : {test_metrics['recall']:.4f}")
    print(f"  F1        : {test_metrics['f1']:.4f}")
    if test_metrics.get("roc_auc") is not None:
        print(f"  ROC-AUC   : {test_metrics['roc_auc']:.4f}")
    print(f"  CV F1     : {test_metrics['cv_f1_mean']:.4f} +/- {test_metrics['cv_f1_std']:.4f}")
    print(f"  Confusion : {test_metrics['confusion_matrix']}")

    return pipeline, test_metrics, importances


# ---------------------------------------------------------------------------
# Main training pipeline
# ---------------------------------------------------------------------------

def train(
    source: str = "custom",
    random_state: int = 42,
) -> Tuple[Any, Any, Metrics, Metrics]:
    """
    Full training pipeline.

    Builds one sklearn Pipeline per model:
    - LogisticRegression: StandardScaler -> LogisticRegression (scaling inside
      the pipeline, fit only on training folds/data — no leakage)
    - RandomForest: no scaler (tree models are scale-invariant)

    Both pipelines are fit on the SAME unscaled X_train and evaluated on the
    SAME unscaled X_test. Each fitted pipeline is saved as a single .pkl.

    Returns: (best_pipeline, best_name, best_metrics, comparison_metrics)
    """
    _ensure_dirs()
    print(f"[train] Loading data from: {source}")
    df = load_training_data(source)

    print(f"[train] Dataset: {len(df)} URLs "
          f"({df['label'].sum()} phishing, {(1 - df['label']).sum()} legit)")
    print(f"[train] Class ratio (phish/total): {df['label'].mean():.3f}")

    # Extract features (unscaled — the LR pipeline scales internally)
    print("[train] Extracting features...")
    X = build_feature_matrix(df["url"])
    y = df["label"].values
    feature_names = get_feature_names()

    # Stratified 80/20 split on raw (unscaled) features
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=random_state
    )
    print(f"[train] Train: {len(X_train)}, Test: {len(X_test)}")

    # ------------------------------------------------------------------
    # Logistic Regression: scaler lives inside the pipeline
    # ------------------------------------------------------------------
    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=random_state,
            solver="lbfgs",
        )),
    ])
    lr_model, lr_metrics, _ = train_and_evaluate(
        lr_pipeline, X_train, X_test, y_train, y_test,
        "LogisticRegression", feature_names,
    )

    # ------------------------------------------------------------------
    # Random Forest: no scaler — trees are scale-invariant
    # ------------------------------------------------------------------
    rf_pipeline = Pipeline([
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )),
    ])
    rf_model, rf_metrics, rf_importances = train_and_evaluate(
        rf_pipeline, X_train, X_test, y_train, y_test,
        "RandomForest", feature_names,
    )

    # ------------------------------------------------------------------
    # Compare and pick best
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("MODEL COMPARISON")
    print("=" * 60)

    comparison: Dict[str, Any] = {
        "LogisticRegression": lr_metrics,
        "RandomForest": rf_metrics,
    }

    # Pick best by F1
    if rf_metrics["f1"] >= lr_metrics["f1"]:
        best_model = rf_model
        best_metrics = rf_metrics
        best_name = "RandomForest"
        best_importances = rf_importances
        save_feature_importances(rf_importances, feature_names, best_name)
        print(f"\n>>> Best model: {best_name} (F1={best_metrics['f1']:.4f})")
        print(f"    Saved to models/{best_name}.pkl")
    else:
        best_model = lr_model
        best_metrics = lr_metrics
        best_name = "LogisticRegression"
        best_importances = None
        print(f"\n>>> Best model: {best_name} (F1={best_metrics['f1']:.4f})")
        print(f"    Saved to models/{best_name}.pkl")

    # Save both fitted pipelines (single .pkl each, scaler embedded where present)
    save_model(rf_model, "RandomForest")
    save_model(lr_model, "LogisticRegression")

    # Save comparison report
    save_report({
        "dataset": source,
        "n_samples": int(len(df)),
        "n_phishing": int(df["label"].sum()),
        "n_legitimate": int((1 - df["label"]).sum()),
        "class_balance_ratio": float(df["label"].mean()),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "comparison": comparison,
        "best_model": best_name,
        "best_metrics": best_metrics,
        "feature_names": feature_names,
        "excluded_features": [_DOMAIN_AGE_NOTE],
    }, "training_report.json")

    # Keep the optional PhishGuard web-app export in sync with THIS run
    # (reads reports/training_report.json, so it must run after save_report).
    # Best-effort: never let the out-of-scope export break training.
    if _export_web_model is not None:
        try:
            _export_web_model()
        except Exception as exc:
            print(f"[train] NOTE: web-app model export failed (non-fatal): {exc}")

    return best_model, best_name, best_metrics, comparison


def save_model(model: Any, name: str):
    """Save a fitted Pipeline as a single .pkl to models/."""
    joblib.dump(model, MODELS_DIR / f"{name}.pkl")
    print(f"[train] Saved fitted pipeline to models/{name}.pkl")


def save_feature_importances(
    importances: np.ndarray,
    feature_names: list,
    model_name: str,
):
    """Save feature importances CSV + bar chart PNG."""
    df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=True)

    df.to_csv(REPORTS_DIR / f"{model_name}_feature_importances.csv", index=False)
    print(f"[train] Feature importances saved to reports/{model_name}_feature_importances.csv")

    # Plot
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot.barh(x="feature", y="importance", ax=ax, legend=False)
        ax.set_title(f"{model_name} — Feature Importances")
        ax.set_xlabel("Mean Decrease in Impurity")
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / f"{model_name}_feature_importances.png", dpi=150)
        plt.close()
        print(f"[train] Feature importance plot saved to reports/{model_name}_feature_importances.png")
    except Exception as exc:
        print(f"[train] Could not save feature importance plot: {exc}")


def save_report(report: Dict[str, Any], filename: str):
    """Save a JSON report to reports/."""
    path = REPORTS_DIR / filename
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[train] Report saved to reports/{filename}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train phishing URL detection models")
    parser.add_argument(
        "--source",
        choices=["uci", "custom"],
        default="custom",
        help="Dataset source (default: custom)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PHISHING DETECTOR — MODEL TRAINING")
    print("=" * 60)

    try:
        best_model, best_name, best_metrics, comparison = train(
            source=args.source,
            random_state=args.seed,
        )
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print("=" * 60)
    except FileNotFoundError as exc:
        print(f"\nError: {exc}")
        print("\nTo fix: download a dataset first.")
        print("  UCI:   python -m src.fetch_data")
        print("  Custom: python -m src.fetch_data --custom")
        raise SystemExit(1)
    except Exception as exc:
        print(f"\nUnexpected error: {exc}")
        raise
