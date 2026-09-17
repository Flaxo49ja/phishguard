"""
check_url_test.py - Regression tests for the CLI (check_url.py).

Two kinds of proof:

1. GOLDEN MASTER: replays 8 real URLs through the exact main() flow and
   compares the full JSON response (verdict, probability, all 18 features,
   per-feature occlusion contributions, benign baseline) against
   check_url_golden.json, captured from the pre-optimization implementation.
   Any change in outputs - even a float in the 4th decimal - fails the suite.

2. CALL-COUNT (performance contract): _format_output's occlusion explanation
   must classify all counterfactual variants in ONE batched predict_proba
   call. The pre-optimization implementation calls the pipeline once per
   feature (18) plus base plus baseline = 20 times per URL; this test fails
   until the batched implementation lands.

Run:  .venv/bin/python src/check_url_test.py
"""

import json
import math
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

try:  # package mode or script mode
    from . import check_url as cu
except ImportError:
    import check_url as cu

try:  # package mode or script mode
    from .features import get_feature_names
except ImportError:
    from features import get_feature_names

GOLDEN_PATH = SRC_DIR / "check_url_golden.json"
THRESHOLD = 0.5
# One batched predict_proba for the whole occlusion explanation (base row +
# one row per occluded feature + benign baseline all go in a single matrix).
EXPECTED_PROBA_CALLS_PER_EXPLANATION = 1


class _CountingPipeline:
    """Delegates everything to the real pipeline; counts predict_proba calls."""

    def __init__(self, pipeline):
        self._pipeline = pipeline
        self.proba_calls = 0

    def predict_proba(self, X):
        self.proba_calls += 1
        return self._pipeline.predict_proba(X)

    def predict(self, X):
        return self._pipeline.predict(X)

    def __getattr__(self, name):
        return getattr(self._pipeline, name)


def _first_difference(got, expected, path="response"):
    """Human-readable pointer to the first differing leaf, for failure output."""
    if isinstance(got, dict) and isinstance(expected, dict):
        for key in sorted(set(got) | set(expected)):
            if key not in got:
                return f"{path}.{key}: missing (expected {expected[key]!r})"
            if key not in expected:
                return f"{path}.{key}: unexpected value {got[key]!r}"
            diff = _first_difference(got[key], expected[key], f"{path}.{key}")
            if diff:
                return diff
        return None
    if isinstance(got, list) and isinstance(expected, list):
        if len(got) != len(expected):
            return f"{path}: length {len(got)} != expected {len(expected)}"
        for i, (g, e) in enumerate(zip(got, expected)):
            diff = _first_difference(g, e, f"{path}[{i}]")
            if diff:
                return diff
        return None
    if got != expected:
        return f"{path}: got {got!r}, expected {expected!r}"
    return None


def _lr_proba(rows, lr_pipeline):
    """Real LR pipeline probabilities for a batch of plain-python rows."""
    import numpy as np

    return lr_pipeline.predict_proba(np.asarray(rows, dtype=np.float64))[:, 1]


def run_fast_tests(golden):
    """Fast-path tests (--fast: numpy/sklearn-free inference via lr_fast.json).

    1. models/lr_fast.json must exist and be FRESH (not older than the LR
       pickle it was exported from).
    2. Pure-python fast inference must match the real LogisticRegression
       pipeline to 1e-6 on every golden URL.
    """
    failures = []
    total = 0

    print("\n" + "=" * 70)
    print("FAST PATH TESTS (--fast)")
    print("=" * 70)

    # --- fast model file exists, is fresh, and has the right shape --------
    total += 1
    try:
        fast = cu._load_fast_model()
        ok_shape = (
            fast.get("featureNames") == get_feature_names()
            and len(fast.get("weights", [])) == len(get_feature_names())
            and len(fast.get("scaler", {}).get("means", [])) == len(get_feature_names())
            and len(fast.get("scaler", {}).get("stds", [])) == len(get_feature_names())
            and isinstance(fast.get("bias"), (int, float))
        )
        if ok_shape:
            print("  OK models/lr_fast.json exists, fresh, structurally valid")
        else:
            failures.append(("lr_fast.json", "exists but featureNames/scaler/weights/bias malformed"))
    except Exception as exc:  # noqa: BLE001
        failures.append(("lr_fast.json", f"_load_fast_model raised {type(exc).__name__}: {exc}"))

    # --- fast inference parity vs the real LR pipeline ---------------------
    try:
        fast = cu._load_fast_model()
        lr_pipeline = cu._load_pipeline("LogisticRegression")

        for case in golden:
            raw = case["raw_input"]
            total += 1
            url = cu._prepare_input(raw)
            feats = cu.extract_features(url)

            names = get_feature_names()
            x = [[float(feats[n]) for n in names]]
            real_prob = float(_lr_proba(x, lr_pipeline)[0])
            fast_prob = cu._fast_proba(fast, feats)

            if abs(real_prob - fast_prob) <= 1e-6:
                print(f"  OK {raw[:52]:54s} p={fast_prob:.6f} (== LR pipeline)")
            else:
                failures.append(
                    (raw, f"fast p={fast_prob:.8f} vs LR pipeline p={real_prob:.8f} (diff {abs(real_prob-fast_prob):.2e})")
                )

        # sigmoid sanity: _fast_proba must actually use the logistic function
        total += 1
        z_probe = {n: 0.0 for n in get_feature_names()}
        p0 = cu._fast_proba(fast, z_probe)
        z = fast["bias"]
        for j, n in enumerate(names):
            z += fast["weights"][j] * ((0.0 - fast["scaler"]["means"][j]) / fast["scaler"]["stds"][j])
        if abs(p0 - (1 / (1 + math.exp(-z)))) <= 1e-12:
            print("  OK sigmoid(z) formula verified against closed form")
        else:
            failures.append(("sigmoid", f"_fast_proba(zero feats)={p0} != closed form {1/(1+math.exp(-z))}"))
    except Exception as exc:  # noqa: BLE001
        failures.append(("fast parity", f"could not run: {type(exc).__name__}: {exc}"))

    return failures, total


def run_tests():
    """Run all regression tests. Returns 0 on success, 1 on failure."""
    failures = []
    total = 0

    print("=" * 70)
    print("CHECK_URL REGRESSION TESTS")
    print("=" * 70)

    golden = json.loads(GOLDEN_PATH.read_text())
    pipeline = cu._load_pipeline("RandomForest")

    calls_seen = []

    for case in golden:
        raw = case["raw_input"]
        total += 1
        try:
            url = cu._prepare_input(raw)
            _, prob, feats = cu._extract_and_predict(url, pipeline)
            pred = 1 if prob >= THRESHOLD else 0

            counter = _CountingPipeline(pipeline)
            js = cu._format_output(url, pred, prob, feats, counter, json_output=True)
            calls_seen.append(counter.proba_calls)

            got = json.loads(js)
            diff = _first_difference(got, case["response"])
            if diff:
                failures.append((raw, f"golden mismatch: {diff}"))
            else:
                resp = got
                print(f"  OK {raw[:52]:54s} {resp['verdict']:11s} p={resp['phishing_probability']}")
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append((raw, f"unexpected {type(exc).__name__}: {exc}"))

    # Performance contract: occlusion explanation is one batched call per URL.
    total += 1
    worst = max(calls_seen) if calls_seen else -1
    if any(c != EXPECTED_PROBA_CALLS_PER_EXPLANATION for c in calls_seen):
        failures.append(
            (
                "pipeline call count",
                f"occlusion explanation used up to {worst} predict_proba calls per URL "
                f"(expected {EXPECTED_PROBA_CALLS_PER_EXPLANATION}); "
                "counterfactual rows must be classified in one batch",
            )
        )
    else:
        print(
            f"  OK occlusion explanation: {EXPECTED_PROBA_CALLS_PER_EXPLANATION} "
            f"batched predict_proba call per URL"
        )

    # Fast path (--fast): pure-python inference parity + freshness contract
    fast_failures, fast_total = run_fast_tests(golden)
    failures.extend(fast_failures)
    total += fast_total

    print("\n" + "=" * 70)
    if failures:
        print(f"FAILED: {len(failures)}/{total} tests")
        for label, msg in failures:
            print(f"  - {label}: {msg}")
        return 1
    print(f"ALL PASSED: {total}/{total} tests")
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
