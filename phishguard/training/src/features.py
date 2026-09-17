"""
features.py - Extract lexical/structural features from a URL.

Every function is pure (no network calls, no `requests`, no WHOIS).
Use urllib.parse for everything.

Usage:
    from features import extract_features
    feats = extract_features("https://example.com/path")
"""

import math
import re
from collections import Counter
from collections.abc import Callable
from typing import Any, Dict, List, Tuple

from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Known URL shorteners (lowercased, without scheme)
# ---------------------------------------------------------------------------
SHORTENER_DOMAINS = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "buff.ly",
    "shorturl.at", "is.gd", "sourc.in", "cli.gs", "tr.im", "v.gd",
    "tiny.cc", "snip.ly", "cutt.ly", "adf.ly", "shorte.st", "bc.vc",
    "da.gd", "qr.io", "rb.gy", "0.gp", "alturls.com", "xxa.me",
    "bcz.im", "shoort.com", "short.link", "b23.tv", "tiny.cc",
    "u.to", "vzt.url", "shorturl.ms", "twurl.cc", "p.tl",
})

# Regex patterns
_IPV4_REGEX = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$"
)
_DOMAIN_AGE_NOTE = (
    "domain_age_flag deliberately excluded: requires WHOIS/network access "
    "and breaks the offline-only inference guarantee."
)


# ===========================================================================
# Individual feature functions
# ===========================================================================

def _parse_url(url: str) -> urlparse:
    """Parse a URL string; auto-prepend http:// if no scheme present."""
    if not url.startswith(("http://", "https://", "ftp://")):
        url = "http://" + url
    try:
        parsed = urlparse(url)
    except ValueError:
        # Malformed URL (e.g. Invalid IPv6 URL from stray brackets).
        # Strip bracketed fragments and retry once, else degrade gracefully.
        cleaned = url.replace("[", "").replace("]", "")
        try:
            parsed = urlparse(cleaned)
        except ValueError:
            parsed = urlparse("http://invalid/")
    if not parsed.hostname:
        # Fallback: treat whole string as hostname-ish
        try:
            parsed = urlparse("http://" + url)
        except ValueError:
            parsed = urlparse("http://invalid/")
    return parsed


def url_length(url: str) -> int:
    """Total character length of the URL string."""
    return len(url)


def hostname_length(url: str) -> int:
    """Length of the hostname (domain) portion."""
    return len(_parse_url(url).hostname or "")


def path_length(url: str) -> int:
    """Length of the URL path (excluding query and fragment)."""
    return len(_parse_url(url).path or "")


def num_dots(url: str) -> int:
    """Count of '.' characters in the full URL."""
    return url.count(".")


def num_hyphens(url: str) -> int:
    """Count of '-' characters in the full URL."""
    return url.count("-")


def num_underscores(url: str) -> int:
    """Count of '_' characters in the full URL."""
    return url.count("_")


def num_slashes(url: str) -> int:
    """Count of '/' characters in the full URL."""
    return url.count("/")


def num_digits(url: str) -> int:
    """Count of digit characters (0-9) in the URL."""
    return sum(1 for c in url if c.isdigit())


def num_special_chars(url: str) -> int:
    """
    Count of suspicious special characters: @, %, =, &, ?, #, +, $, ,.
    (These are often used to obfuscate or inject parameters.)
    """
    special = set("@%=&?#+$,")
    return sum(1 for c in url if c in special)


def has_at_symbol(url: str) -> int:
    """1 if '@' is present in the URL, else 0. (bool -> int for ML)"""
    return 1 if "@" in url else 0


def has_ip_address(url: str) -> int:
    """
    1 if the hostname looks like a raw IPv4 address, else 0.

    Phishers sometimes serve pages from bare IPs to avoid domain-based
    blocking and to hide the true operator.
    """
    hostname = _parse_url(url).hostname or ""
    return 1 if _IPV4_REGEX.match(hostname) else 0


def num_subdomains(url: str) -> int:
    """
    Number of subdomain label segments beyond the registered domain.

    Heuristic: count dots in hostname, subtract 1 for the registered
    domain + TLD. A hostname like "a.b.c.example.com" -> 3 subdomains.
    """
    hostname = _parse_url(url).hostname or ""
    parts = [p for p in hostname.split(".") if p]
    if len(parts) <= 2:
        return 0
    return len(parts) - 2


def uses_https(url: str) -> int:
    """1 if the scheme is https, else 0."""
    return 1 if _parse_url(url).scheme == "https" else 0


def has_https_token_in_path(url: str) -> int:
    """
    1 if the literal string 'https' appears in the path portion.

    Phishing URLs sometimes stuff "https" or a brand name into the path
    or subdomain to *look* secure/legitimate.
    """
    path = _parse_url(url).path.lower()
    return 1 if "https" in path else 0


def is_shortened_url(url: str) -> int:
    """
    1 if the hostname matches a known URL-shortener domain, else 0.
    """
    hostname = (_parse_url(url).hostname or "").lower()
    # Check exact match or subdomain-of-shortener
    for shortener in SHORTENER_DOMAINS:
        if hostname == shortener or hostname.endswith("." + shortener):
            return 1
    return 0


def url_entropy(url: str) -> float:
    """
    Shannon entropy of the URL string (byte-level).

    Higher entropy = more "random-looking" = often a sign of generated
    phishing URLs.
    """
    if not url:
        return 0.0
    freq = Counter(url)
    length = len(url)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 4)


def tld_in_subdomain(url: str) -> int:
    """
    1 if a known top-level domain (e.g. .com, .ru, .net) appears as a
    *subdomain* label — a pattern like paypal.com.verify-login.ru.

    This is a strong phishing signal because it mimics the visual
    appearance of a legitimate domain.

    Exemption: a TLD-looking label that is the direct second-level of a
    2-letter ccTLD (e.g. the 'co' in bbc.co.uk, 'com' in example.com.au)
    is a legitimate multi-part suffix, NOT a homograph trick, so it does
    not fire. A label like 'com' in paypal.com.verify-login.ru still
    fires because it is followed by another label, not the ccTLD.
    """
    hostname = _parse_url(url).hostname or ""
    parts = [p.lower() for p in hostname.split(".") if p]
    if len(parts) < 3:
        return 0

    # Common TLDs to check — we check if any middle segment *is* a TLD
    common_tlds = {
        "com", "net", "org", "edu", "gov", "mil", "int",
        "ru", "cn", "de", "fr", "uk", "nl", "au", "ca",
        "jp", "kr", "br", "it", "es", "pl", "in", "za",
        "info", "biz", "name", "pro", "mobi", "co", "io",
        "app", "dev", "xyz", "club", "online", "site",
        "shop", "tech", "top", "download", "loan", "work",
    }

    final = parts[-1]
    for i, part in enumerate(parts[:-1]):
        if part not in common_tlds:
            continue
        # Skip ccTLD second-level labels: 'co' in bbc.co.uk is position
        # len-2 with a 2-letter final label directly after it.
        if i == len(parts) - 2 and len(final) == 2:
            continue
        return 1
    return 0


def digit_letter_ratio(url: str) -> float:
    """
    Ratio of digits to letters (a-z, A-Z) in the URL.

    Returns 0.0 if no letters present.
    """
    letters = sum(1 for c in url if c.isalpha())
    digits = sum(1 for c in url if c.isdigit())
    if letters == 0:
        return 0.0
    return round(digits / letters, 4)


# ===========================================================================
# Feature registry + aggregator
# ===========================================================================

_FEATURE_FUNCTIONS: List[Tuple[str, Callable[[str], Any]]] = [
    ("url_length", url_length),
    ("hostname_length", hostname_length),
    ("path_length", path_length),
    ("num_dots", num_dots),
    ("num_hyphens", num_hyphens),
    ("num_underscores", num_underscores),
    ("num_slashes", num_slashes),
    ("num_digits", num_digits),
    ("num_special_chars", num_special_chars),
    ("has_at_symbol", has_at_symbol),
    ("has_ip_address", has_ip_address),
    ("num_subdomains", num_subdomains),
    ("uses_https", uses_https),
    ("has_https_token_in_path", has_https_token_in_path),
    ("is_shortened_url", is_shortened_url),
    ("url_entropy", url_entropy),
    ("tld_in_subdomain", tld_in_subdomain),
    ("digit_letter_ratio", digit_letter_ratio),
]


def extract_features(url: str) -> Dict[str, Any]:
    """
    Extract all 18 lexical/structural features from a single URL.

    Returns a dict {feature_name: value} suitable for passing to a
    scikit-learn model via pd.DataFrame([feats]).

    Raises ValueError on empty/untrustworthy input.
    """
    if not url or not url.strip():
        raise ValueError("URL must be non-empty")

    parsed = _parse_url(url.strip())
    if not parsed.hostname:
        raise ValueError(f"Could not parse hostname from URL: {url}")

    try:
        return {name: func(url.strip()) for name, func in _FEATURE_FUNCTIONS}
    except ValueError:
        # Malformed URL (e.g. Invalid IPv6 URL) — degrade gracefully with
        # neutral feature values so batch extraction never crashes.
        return {name: 0 for name, _ in _FEATURE_FUNCTIONS}


def get_feature_names() -> List[str]:
    """Return the ordered list of feature names (matches extract_features output)."""
    return [name for name, _ in _FEATURE_FUNCTIONS]


def get_feature_list() -> List[Callable[[str], Any]]:
    """Return the ordered list of feature callables (for external pipelines)."""
    return [func for _, func in _FEATURE_FUNCTIONS]


# ===========================================================================
# Batch helper
# ===========================================================================

def extract_features_batch(urls: List[str]) -> List[Dict[str, Any]]:
    """Extract features for multiple URLs; skips URLs that fail with a warning."""
    results: List[Dict[str, Any]] = []
    for url in urls:
        try:
            results.append(extract_features(url))
        except ValueError as exc:
            print(f"[features] Skipping invalid URL '{url}': {exc}")
    return results


if __name__ == "__main__":
    # Quick smoke test
    test_urls = [
        "https://www.google.com/search?q=hello",
        "http://192.168.1.1/admin",
        "https://bit.ly/3xample",
        "http://paypal.com.verify-login.ru/secure",
        "https://a.b.c.d.example.com/very/long/path/here",
    ]

    for u in test_urls:
        print(f"\nURL: {u}")
        feats = extract_features(u)
        for k, v in feats.items():
            print(f"  {k:30s} = {v}")
