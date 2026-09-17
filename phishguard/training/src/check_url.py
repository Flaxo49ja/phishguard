#!/usr/bin/env python3
"""
check_url.py — CLI tool to classify URLs as phishing or legitimate.

Usage:
    python check_url.py <url>
    python check_url.py <url> --json

Loads the trained pipeline at startup (each models/<name>.pkl is a full
sklearn Pipeline — any scaling lives inside it), extracts features from the
input URL, and prints the verdict + phishing probability.

NO network calls are made to the URL. Everything is lexical/structural.

Fast mode (--fast): runs the exported LogisticRegression in pure Python
(models/lr_fast.json — ~2 KB of weights, no sklearn, no numpy, no joblib).
Starts in ~0.3 s instead of ~20 s; predictions match the LR pipeline to
6 decimal places (guarded by check_url_test.py).
"""

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# NOTE: joblib/numpy are imported LAZILY inside _load_pipeline /
# _extract_and_predict so that --fast mode (pure-python inference) never pays
# the ~2 s joblib+numpy import cost — and never imports sklearn at all.

# Match train.py/evaluate.py convention: keep sklearn's parallel-worker
# UserWarnings out of CLI output (pure noise for end users).
warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
FAST_MODEL_PATH = MODELS_DIR / "lr_fast.json"

try:  # package mode (python -m src.check_url) or script mode (python src/check_url.py)
    from .features import extract_features, get_feature_names
except ImportError:
    from features import extract_features, get_feature_names

DEFAULT_MODEL = "RandomForest"
THRESHOLD = 0.5


def _load_pipeline(model_name: str = DEFAULT_MODEL) -> Any:
    """Load the trained pipeline (preprocessing + classifier in one .pkl)."""
    model_path = MODELS_DIR / f"{model_name}.pkl"

    if not model_path.exists():
        print(
            f"Error: Model not found at {model_path}\n"
            "Run training first: python -m src.train",
            file=sys.stderr,
        )
        sys.exit(1)

    import joblib  # lazy: not needed in --fast mode

    return joblib.load(model_path)


def _load_fast_model() -> Dict[str, Any]:
    """Load the exported pure-python LR model (models/lr_fast.json).

    If the file is missing or older than the LogisticRegression pickle it
    mirrors, regenerate it via export_model.export() (best-effort) so the
    fast path can never silently drift from the trained pipeline.
    """
    lr_pkl = MODELS_DIR / "LogisticRegression.pkl"
    is_fresh = FAST_MODEL_PATH.exists() and (
        not lr_pkl.exists() or FAST_MODEL_PATH.stat().st_mtime >= lr_pkl.stat().st_mtime
    )
    if not is_fresh:
        try:  # package mode or script mode
            from .export_model import export as _export_fast_model
        except ImportError:
            try:
                from export_model import export as _export_fast_model
            except ImportError:
                _export_fast_model = None
        if _export_fast_model is None:
            raise FileNotFoundError(
                f"{FAST_MODEL_PATH} not found. Generate it: python -m src.export_model"
            )
        _export_fast_model()

    return json.loads(FAST_MODEL_PATH.read_text())


def _fast_proba(fast_model: Dict[str, Any], feats: Dict[str, Any]) -> float:
    """Pure-python LR inference: sigmoid(bias + w . (x - mean)/std).

    Mathematically identical to the sklearn pipeline (verified to 1e-6 by
    check_url_test.py). No numpy, no sklearn — safe to call before any
    heavy imports.
    """
    means = fast_model["scaler"]["means"]
    stds = fast_model["scaler"]["stds"]
    weights = fast_model["weights"]
    z = fast_model["bias"]
    for j, name in enumerate(fast_model["featureNames"]):
        xj = feats[name]
        if isinstance(xj, bool):
            xj = 1 if xj else 0
        z += weights[j] * ((float(xj) - means[j]) / stds[j])
    if z < -500.0:
        return 0.0
    if z > 500.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def _fast_proba_rows(fast_model: Dict[str, Any], rows: List[List[float]]) -> List[float]:
    """Batch version of _fast_proba on pre-built feature rows (feature order
    == fast_model['featureNames']). Pure python — no numpy needed."""
    means = fast_model["scaler"]["means"]
    stds = fast_model["scaler"]["stds"]
    weights = fast_model["weights"]
    bias = fast_model["bias"]
    out: List[float] = []
    for row in rows:
        z = bias
        for j, xj in enumerate(row):
            z += weights[j] * ((xj - means[j]) / stds[j])
        if z < -500.0:
            out.append(0.0)
        elif z > 500.0:
            out.append(1.0)
        else:
            out.append(1.0 / (1.0 + math.exp(-z)))
    return out


def _prepare_input(url: str) -> str:
    """
    Basic input validation: ensure URL has a scheme, normalize.

    If no scheme is present, assume http://.
    """
    url = url.strip()
    if not url:
        print("Error: URL cannot be empty.", file=sys.stderr)
        sys.exit(1)

    if not url.startswith(("http://", "https://", "ftp://")):
        url = "http://" + url
        print(f"Note: No scheme detected. Assumed http:// — checking: {url}")

    return url


def _extract_and_predict(
    url: str,
    pipeline: Any,
) -> Tuple[int, float, Dict[str, Any]]:
    """
    Extract features, then let the pipeline predict.

    Returns: (prediction_class, probability, feature_dict)
    """
    try:
        feats = extract_features(url)
    except ValueError as exc:
        print(f"Error extracting features: {exc}", file=sys.stderr)
        sys.exit(1)

    import numpy as np  # lazy: not needed in --fast mode

    feature_names = get_feature_names()
    # Plain numpy row (pandas import removed: it cost ~1.4 s of startup for
    # a single 1x18 matrix). Column order == get_feature_names() order, which
    # is exactly what the pipelines were trained on.
    X = np.array([[float(feats[name]) for name in feature_names]], dtype=np.float64)

    pred = int(pipeline.predict(X)[0])
    prob = float(pipeline.predict_proba(X)[0, 1])

    return pred, prob, feats


def _extract_and_predict_fast(
    url: str,
    fast_model: Dict[str, Any],
) -> Tuple[int, float, Dict[str, Any]]:
    """Fast-mode twin of _extract_and_predict: pure-python inference."""
    try:
        feats = extract_features(url)
    except ValueError as exc:
        print(f"Error extracting features: {exc}", file=sys.stderr)
        sys.exit(1)

    prob = _fast_proba(fast_model, feats)
    pred = 1 if prob >= THRESHOLD else 0
    return pred, prob, feats


# Benign-typical reference values for each feature (medians of the legitimate
# class: short hostnames, few separators, no '@', https, low digit ratio, ...).
# Used for per-URL explanations: each feature is swapped to this value one at
# a time and the change in phishing probability is measured (occlusion).
_BENIGN_REFERENCE: Dict[str, float] = {
    "url_length": 45.0,
    "hostname_length": 15.0,
    "path_length": 10.0,
    "num_dots": 2.0,
    "num_hyphens": 0.0,
    "num_underscores": 0.0,
    "num_slashes": 2.0,
    "num_digits": 0.0,
    "num_special_chars": 0.0,
    "has_at_symbol": 0.0,
    "has_ip_address": 0.0,
    "num_subdomains": 1.0,
    "uses_https": 1.0,
    "has_https_token_in_path": 0.0,
    "is_shortened_url": 0.0,
    "url_entropy": 3.3,
    "tld_in_subdomain": 0.0,
    "digit_letter_ratio": 0.03,
}


def _explain_prediction(
    pipeline: Any,
    feats: Dict[str, Any],
    n: int = 8,
) -> Tuple[float, List[Dict[str, Any]], float]:
    """
    Explain THIS prediction via one-at-a-time occlusion.

    For every feature: replace its value with the benign-typical reference
    and re-run the pipeline. contribution = base_prob - counterfactual_prob,
    so a positive contribution means the feature pushed the verdict toward
    PHISHING, negative toward LEGITIMATE.

    Note: this is an approximation (interactions between features are not
    captured and contributions may not sum to the base probability).

    Returns: (base_prob, contributions_sorted_by_abs, benign_baseline_prob)
      where benign_baseline_prob is the phishing probability if ALL features
      were set to the benign reference at once.
    """
    feature_names = get_feature_names()
    base_row = [float(feats[name]) for name in feature_names]

    # Batch ALL counterfactual rows into ONE predict_proba call:
    #   row 0        = the actual URL's features (base)
    #   rows 1..n    = one row per occluded feature (swapped to benign ref)
    #   last row     = all-benign reference (the benign baseline)
    # This is mathematically identical to the old one-call-per-feature loop
    # but turns 20 pipeline invocations into 1 (was ~5.6 s, now ~0.7 s).
    ref_indices = [
        (idx, _BENIGN_REFERENCE[name])
        for idx, name in enumerate(feature_names)
        if name in _BENIGN_REFERENCE
    ]
    rows = [list(base_row)]
    for idx, ref in ref_indices:
        row = list(base_row)
        row[idx] = float(ref)
        rows.append(row)
    rows.append([float(_BENIGN_REFERENCE[name]) for name in feature_names])

    if isinstance(pipeline, dict):
        # Fast mode: pure-python batch inference on the exported LR model.
        probs = _fast_proba_rows(pipeline, rows)
    else:
        import numpy as np  # lazy: not needed in --fast mode

        # Batch ALL counterfactual rows into ONE predict_proba call:
        #   row 0        = the actual URL's features (base)
        #   rows 1..n    = one row per occluded feature (swapped to benign ref)
        #   last row     = all-benign reference (the benign baseline)
        # This is mathematically identical to the old one-call-per-feature loop
        # but turns 20 pipeline invocations into 1 (was ~5.6 s, now ~0.7 s).
        X = np.array(rows, dtype=np.float64)
        probs = [float(p) for p in pipeline.predict_proba(X)[:, 1]]

    base_prob = float(probs[0])
    benign_prob = float(probs[-1])

    contributions: List[Dict[str, Any]] = []
    for pos, (idx, _) in enumerate(ref_indices, start=1):
        name = feature_names[idx]
        c = base_prob - float(probs[pos])
        # Direction is derived from the ROUNDED contribution so the output is
        # deterministic: RandomForest's parallel summation adds ~1e-16 noise,
        # which used to flip the sign (and the printed direction) of exact-zero
        # contributions between runs.
        rc = round(c, 4)
        direction = "phishing" if rc > 0 else ("legitimate" if rc < 0 else "neutral")
        contributions.append(
            {"feature": name, "value": feats[name], "contribution": rc, "direction": direction}
        )

    contributions.sort(key=lambda d: abs(d["contribution"]), reverse=True)

    return base_prob, contributions, benign_prob


def _format_output(
    url: str,
    pred: int,
    prob: float,
    feats: Dict[str, Any],
    pipeline: Any,
    json_output: bool = False,
) -> str:
    """Format the prediction result for display."""
    verdict = "PHISHING" if pred == 1 else "LEGITIMATE"
    _, contributions, benign_prob = _explain_prediction(pipeline, feats)

    if json_output:
        output: Dict[str, Any] = {
            "url": url,
            "verdict": verdict,
            "phishing_probability": round(prob, 4),
            "threshold": THRESHOLD,
            "features": dict(feats),
            "feature_contributions": contributions,
            "benign_baseline_probability": round(benign_prob, 4),
        }
        return json.dumps(output, indent=2)

    lines = [
        f"URL: {url}",
        f"Verdict: {verdict}",
        f"Phishing probability: {prob:.4f}",
        "",
        "Top feature contributions (toward PHISHING + / toward LEGITIMATE −):",
    ]
    for c in contributions:
        lines.append(
            f"  - {c['feature']} = {c['value']} → {c['contribution']:+.4f} ({c['direction']})"
        )
    lines.append("")
    lines.append(
        f"Benign baseline: {benign_prob:.4f} — probability if every feature were benign-typical"
    )

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Classify a URL as phishing or legitimate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_url.py https://www.google.com
  python check_url.py http://paypal.com.verify-login.ru/secure --json
  python check_url.py bit.ly/3xample
  python check_url.py https://www.google.com --fast   # <1 s startup
        """,
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL to check (scheme optional, will assume http:// if missing)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model name to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help=(
            "Use the exported LogisticRegression in pure python "
            "(models/lr_fast.json): starts in <1 s, no sklearn/numpy load. "
            "Predictions match the LR pipeline to 6 decimals."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of human-readable text",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=THRESHOLD,
        help=f"Probability threshold for phishing classification (default: {THRESHOLD})",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available saved models and exit",
    )

    args = parser.parse_args(argv)

    # List available models
    if args.list_models:
        models = list(MODELS_DIR.glob("*.pkl"))
        if not models:
            print("No saved models found in models/")
            print("Train one first: python -m src.train")
            return
        print("Available models:")
        for m in models:
            print(f"  - {m.stem}  ({m.name})")
        return

    if not args.url:
        parser.print_help()
        print("\nError: URL argument is required.", file=sys.stderr)
        sys.exit(1)

    # Normalize URL
    url = _prepare_input(args.url)

    if args.fast:
        if args.model != DEFAULT_MODEL:
            print(
                f"Note: --fast uses the exported LogisticRegression; --model {args.model} is ignored."
            )
        try:
            fast_model = _load_fast_model()
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        pred, prob, feats = _extract_and_predict_fast(url, fast_model)
        explain_pipeline: Any = fast_model
    else:
        # Load pipeline
        explain_pipeline = _load_pipeline(args.model)
        # Predict
        pred, prob, feats = _extract_and_predict(url, explain_pipeline)

    # Override threshold if specified
    if prob >= args.threshold:
        pred = 1
    else:
        pred = 0

    # Output
    result = _format_output(url, pred, prob, feats, explain_pipeline, args.json)
    print(result)


if __name__ == "__main__":
    main()
