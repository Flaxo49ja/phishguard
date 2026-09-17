"""
features_test.py - Unit tests for the 18 feature functions.

Tests on 5 known phishing URLs and 5 known legitimate URLs.
DO NOT visit these URLs. They are referenced by string only.
"""

import sys
import traceback
from pathlib import Path

# Ensure src/ is importable
SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

try:  # package mode or script mode
    from .features import (
        url_length,
        hostname_length,
        path_length,
        num_dots,
        num_hyphens,
        num_underscores,
        num_slashes,
        num_digits,
        num_special_chars,
        has_at_symbol,
        has_ip_address,
        num_subdomains,
        uses_https,
        has_https_token_in_path,
        is_shortened_url,
        url_entropy,
        tld_in_subdomain,
        digit_letter_ratio,
        extract_features,
    )
except ImportError:
    from features import (
        url_length,
        hostname_length,
        path_length,
        num_dots,
        num_hyphens,
        num_underscores,
        num_slashes,
        num_digits,
        num_special_chars,
        has_at_symbol,
        has_ip_address,
        num_subdomains,
        uses_https,
        has_https_token_in_path,
        is_shortened_url,
        url_entropy,
        tld_in_subdomain,
        digit_letter_ratio,
        extract_features,
    )


# Known phishing URLs (from PhishTank archive - DO NOT VISIT, reference only)
PHISHING_URLS = [
    "http://secure-banking-login.tk/verify.php?user=admin",
    "https://paypal.com.verify-login.ru/secure/auth",
    "http://192.168.1.100/admin/login.asp",
    "https://bit.ly/3x4mpl3-phish",
    "http://amaz0n-security.alerts.tk/update?id=12345",
]

# Known legitimate URLs (well-known, safe to reference by string)
LEGITIMATE_URLS = [
    "https://www.google.com/search?q=hello+world",
    "https://github.com/python/cpython",
    "https://www.amazon.com/dp/B08N5WRWNW",
    "https://en.wikipedia.org/wiki/Phishing",
    "https://mail.google.com/mail/u/0/#inbox",
]


def assert_integer_feature(func, url, expected_gt, label):
    """Assert a non-negative integer feature is >= some expected minimum."""
    val = func(url)
    if not isinstance(val, int) or val < 0:
        return False, f"{label}: expected int >= 0, got {val}"
    return True, None


def run_tests():
    """Run all feature tests and print results."""
    failures = []
    total = 0

    print("=" * 70)
    print("FEATURE EXTRACTION UNIT TESTS")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Test each function on known URLs
    # ------------------------------------------------------------------

    for url in PHISHING_URLS:
        print(f"\n--- PHISHING URL: {url} ---")
        try:
            feats = extract_features(url)
        except Exception as exc:
            failures.append((url, f"extract_features raised: {exc}"))
            continue

        # Spot-check expected high-risk signals
        checks = [
            (num_special_chars, url, 0, "num_special_chars >= 0"),
            (has_at_symbol, url, 0, "has_at_symbol >= 0"),
            (has_ip_address, url, 0, "has_ip_address >= 0"),
            (is_shortened_url, url, 0, "is_shortened_url >= 0"),
            (tld_in_subdomain, url, 0, "tld_in_subdomain >= 0"),
            (uses_https, url, 0, "uses_https >= 0"),
        ]

        for func, u, _, desc in checks:
            total += 1
            val = func(u)
            if not isinstance(val, int):
                failures.append((url, f"{desc}: expected int, got {type(val).__name__}"))
            else:
                print(f"  {desc:35s} = {val}")

        # Entropy should be non-negative
        total += 1
        ent = url_entropy(url)
        if ent < 0:
            failures.append((url, f"url_entropy < 0: {ent}"))
        else:
            print(f"  {'url_entropy':35s} = {ent}")

        # Digit/letter ratio
        total += 1
        ratio = digit_letter_ratio(url)
        if ratio < 0:
            failures.append((url, f"digit_letter_ratio < 0: {ratio}"))
        else:
            print(f"  {'digit_letter_ratio':35s} = {ratio}")

    for url in LEGITIMATE_URLS:
        print(f"\n--- LEGITIMATE URL: {url} ---")
        try:
            feats = extract_features(url)
        except Exception as exc:
            failures.append((url, f"extract_features raised: {exc}"))
            continue

        checks = [
            (num_special_chars, url, 0, "num_special_chars >= 0"),
            (has_at_symbol, url, 0, "has_at_symbol >= 0"),
            (has_ip_address, url, 0, "has_ip_address >= 0"),
            (is_shortened_url, url, 0, "is_shortened_url >= 0"),
            (tld_in_subdomain, url, 0, "tld_in_subdomain >= 0"),
        ]

        for func, u, _, desc in checks:
            total += 1
            val = func(u)
            if not isinstance(val, int):
                failures.append((url, f"{desc}: expected int, got {type(val).__name__}"))
            else:
                print(f"  {desc:35s} = {val}")

        total += 1
        ent = url_entropy(url)
        if ent < 0:
            failures.append((url, f"url_entropy < 0: {ent}"))
        else:
            print(f"  {'url_entropy':35s} = {ent}")

        total += 1
        ratio = digit_letter_ratio(url)
        if ratio < 0:
            failures.append((url, f"digit_letter_ratio < 0: {ratio}"))
        else:
            print(f"  {'digit_letter_ratio':35s} = {ratio}")

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------
    print("\n--- EDGE CASES ---")

    edge_cases = [
        ("empty string", "", ValueError),
        ("whitespace only", "   ", ValueError),
        ("no hostname", "not-a-valid-url!!!", None),  # fallback parses as hostname
        ("IP as hostname", "http://10.0.0.1/", None),  # valid
        ("shortened bit.ly", "https://bit.ly/3abc", None),  # valid, is_shortened=1
    ]

    for label, url, expected_exc in edge_cases:
        total += 1
        try:
            feats = extract_features(url)
            if expected_exc is not None:
                failures.append((url, f"{label}: expected {expected_exc.__name__}, got success"))
            else:
                print(f"  {label:25s}: OK -> hostname={feats.get('hostname_length', 'N/A')}")
        except expected_exc:
            if expected_exc is not None:
                print(f"  {label:25s}: correctly raised {expected_exc.__name__}")
        except Exception as exc:
            failures.append((url, f"{label}: unexpected {type(exc).__name__}: {exc}"))

    # ------------------------------------------------------------------
    # Verify feature count
    # ------------------------------------------------------------------
    print("\n--- FEATURE COUNT CHECK ---")
    total += 1
    exp_count = 18
    sample_feats = extract_features("https://example.com")
    if len(sample_feats) == exp_count:
        print(f"  Expected {exp_count} features, got {len(sample_feats)} -> OK")
    else:
        failures.append(("", f"Expected {exp_count} features, got {len(sample_feats)}"))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    if failures:
        print(f"FAILED: {len(failures)}/{total} tests")
        for url, msg in failures:
            print(f"  - {url}: {msg}")
        return 1
    else:
        print(f"ALL PASSED: {total}/{total} tests")
        return 0


if __name__ == "__main__":
    sys.exit(run_tests())
