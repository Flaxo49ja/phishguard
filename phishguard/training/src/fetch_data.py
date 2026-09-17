"""
fetch_data.py - Downloads/loads phishing + legitimate URL lists.

Supports:
1. UCI Phishing Websites Dataset (pre-engineered features, benchmark only)
2. Custom pipeline: PhishTank (phishing) + Tranco & ealvaradob benign (legitimate)

Run this once to cache data in data/raw/.
"""

import os
import json
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"


def ensure_data_dir() -> Path:
    """Ensure raw data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


# ---------------------------------------------------------------------------
# UCI Phishing Websites Dataset
# ---------------------------------------------------------------------------

UCI_CSV = DATA_DIR / "uci_phishing.csv"


def download_uci_dataset() -> pd.DataFrame:
    """
    Load the UCI Phishing Websites Dataset and cache it as a CSV.

    The dataset contains ~11,000 URLs with 30 pre-engineered features
    and a binary label (1 = phishing, -1 = legitimate).

    Uses the ucimlrepo package to fetch the canonical copy from the UCI
    ML Repository. Falls back to an already-cached CSV.
    """
    ensure_data_dir()

    if UCI_CSV.exists():
        print(f"[fetch_data] Loading cached UCI dataset from {UCI_CSV}")
        return pd.read_csv(UCI_CSV)

    print("[fetch_data] Downloading UCI Phishing dataset via ucimlrepo ...")
    try:
        from ucimlrepo import fetch_ucirepo
    except Exception as exc:
        print(
            f"[fetch_data] ucimlrepo import failed: {exc}\n"
            "  Install it with: pip install ucimlrepo\n"
            "  Or place uci_phishing.csv manually in data/raw/ and re-run."
        )
        raise

    # UCI dataset ID 327 = "Phishing Websites" (~11k URLs, 30 features).
    uci = fetch_ucirepo(id=327)

    # fetch_ucirepo returns a dotdict: data.features (X), data.targets (y).
    X_df = uci.data.features
    y_df = uci.data.targets

    # Target column in this dataset is named 'result' with values -1 (legit) / 1 (phish).
    df = pd.concat([X_df, y_df], axis=1)
    df.columns = [str(c).strip() for c in df.columns]

    label_col = "result" if "result" in df.columns else df.columns[-1]
    raw = df[label_col]
    if raw.dtype == object:
        raw = pd.to_numeric(raw, errors="coerce")

    df["label"] = (raw > 0).astype(int)  # 1 = phishing, 0 = legitimate
    df.drop(columns=[label_col], inplace=True)

    before = len(df)
    df.dropna(subset=["label"], inplace=True)
    if len(df) < before:
        print(f"[fetch_data] Dropped {before - len(df)} rows with missing labels")

    df.to_csv(UCI_CSV, index=False)
    print(f"[fetch_data] Saved {len(df)} rows to {UCI_CSV}")
    return df


# ---------------------------------------------------------------------------
# Custom feature pipeline data (PhishTank + Tranco)
# ---------------------------------------------------------------------------

PHISHTANK_CSV = DATA_DIR / "phishtank.csv"
TRANCO_CSV = DATA_DIR / "tranco_top10k.csv"
BENIGN_JSON = DATA_DIR / "ealvaradob_urls.json"


def load_benign_urls_json(
    path: Optional[Path] = None,
    n_max: int = 70_000,
) -> pd.DataFrame:
    """
    Load real benign URLs (with paths) from the ealvaradob/phishing-dataset
    'urls' subset (Hugging Face). Sample entries look like:
        {"text": "ebay.com/itm/02-03-...", "label": 0}

    label 0 = benign. Returns a DataFrame with a 'url' column.
    Download: https://huggingface.co/datasets/ealvaradob/phishing-dataset
    (file urls.json) -> data/raw/ealvaradob_urls.json
    """
    path = path or BENIGN_JSON
    if not path.exists():
        raise FileNotFoundError(
            f"Benign URLs JSON not found at {path}. Download urls.json from "
            "https://huggingface.co/datasets/ealvaradob/phishing-dataset "
            "and save as data/raw/ealvaradob_urls.json"
        )
    with open(path) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    if "text" not in df.columns:
        raise KeyError(f"Expected 'text' column in {path}. Got: {list(df.columns)}")
    # Keep only benign rows (label 0)
    df = df[df["label"] == 0]
    df = df.rename(columns={"text": "url"})
    df["url"] = df["url"].astype(str).str.strip()
    df.dropna(subset=["url"], inplace=True)
    df = df[df["url"] != ""]
    # Add https:// scheme if missing
    df["url"] = df["url"].apply(
        lambda u: u if u.startswith(("http://", "https://")) else f"https://{u}"
    )
    df.drop_duplicates(subset=["url"], inplace=True)
    # Random sample so the subset is representative (seeded for reproducibility)
    if len(df) > n_max:
        df = df.sample(n=n_max, random_state=42)
    return df[["url"]]


def load_phishtank_csv(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load a PhishTank CSV export.

    Expected columns: phish_id, url, verified, ... (flexible).
    Returns a DataFrame with at least a 'url' column.
    """
    path = path or PHISHTANK_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"PhishTank CSV not found at {path}. "
            "Download from https://www.phishtank.com/phish_archive.php "
            "and save as data/raw/phishtank.csv"
        )
    df = pd.read_csv(path)
    if "url" not in df.columns:
        # Try common alternate names
        for col in ("uri", "target_url", "URL", "site"):
            if col in df.columns:
                df = df.rename(columns={col: "url"})
                break
        else:
            raise KeyError(f"No URL column found in {path}. Columns: {list(df.columns)}")
    df["url"] = df["url"].astype(str).str.strip()
    df.dropna(subset=["url"], inplace=True)
    df.drop_duplicates(subset=["url"], inplace=True)
    return df[["url"]]


def load_tranco_csv(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load a Tranco top-site list CSV.

    Expected: one URL per row (or a column named 'rank'/'url'/'domain').
    Returns a DataFrame with a 'url' column.
    """
    path = path or TRANCO_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Tranco CSV not found at {path}. "
            "Download from https://tranco-list.eu/ and save as data/raw/tranco_top10k.csv"
        )
    df = pd.read_csv(path, header=None)
    # Heuristic: if single column, that's the URL; if multi-column, first col is
    # Tranco's integer rank, second col is the domain.
    if df.shape[1] == 1:
        df.columns = ["url"]
    else:
        # Column 0 = rank (integer), column 1 = domain
        df = df[[df.columns[1]]].rename(columns={df.columns[1]: "url"})
    df["url"] = df["url"].astype(str).str.strip()
    df.dropna(subset=["url"], inplace=True)
    # Add https:// scheme if missing
    df["url"] = df["url"].apply(
        lambda u: u if u.startswith(("http://", "https://")) else f"https://{u}"
    )
    df.drop_duplicates(subset=["url"], inplace=True)
    return df[["url"]]


def _cap_per_host(df: pd.DataFrame, max_per_host: int) -> pd.DataFrame:
    """
    Keep at most `max_per_host` URLs per hostname (seeded sample).

    Prevents a handful of heavily-repeated hosts (e.g. 5,700+ PhishTank
    URLs on docs.google.com) from letting the model memorize host-level
    patterns instead of learning transferable lexical signals.
    """
    from urllib.parse import urlparse

    def _host(u):
        try:
            return urlparse(u).hostname or ""
        except ValueError:
            return "(invalid)"

    # Shuffle first (seeded) so head(n) keeps a random subset per host
    shuffled = df.sample(frac=1, random_state=42)
    return shuffled.groupby(shuffled["url"].apply(_host)).head(max_per_host)


def build_custom_dataset(
    phishing_path: Optional[Path] = None,
    legit_path: Optional[Path] = None,
    benign_json_path: Optional[Path] = None,
    n_legit: int = 10_000,
    n_benign_with_paths: int = 70_000,
    max_per_host: int = 10,
) -> pd.DataFrame:
    """
    Combine real phishing + legitimate URLs into one CSV.

    Phishing: PhishTank verified feed (online-valid.csv).
    Legitimate:
      - Tranco top sites (bare homepages) — real top-domain traffic
      - ealvaradob benign subset (full URLs with paths) — real deep links
    The ealvaradob benign part is essential: Tranco alone contains ONLY
    bare domains (0% with paths), while ~61% of PhishTank URLs have paths.
    Training on Tranco alone teaches the model 'any path = phishing',
    which is dataset bias, not signal.

    Cross-class dedupe: any URL appearing in BOTH classes is dropped from
    the phishing side (benign label wins) so the same URL never carries
    conflicting labels, and exact train/test leakage via duplicates is
    impossible within a class (exact dedupe happens per class first).

    Output: data/processed/custom_dataset.csv with columns ['url', 'label'].
    label = 1 for phishing, 0 for legitimate.
    """
    phishing_df = load_phishtank_csv(phishing_path)
    tranco_df = load_tranco_csv(legit_path).head(n_legit)
    benign_df = load_benign_urls_json(benign_json_path, n_max=n_benign_with_paths)

    legit_df = pd.concat([tranco_df, benign_df], ignore_index=True)
    legit_df.drop_duplicates(subset=["url"], inplace=True)

    phishing_df = phishing_df.copy()
    phishing_df["label"] = 1
    legit_df = legit_df.copy()
    legit_df["label"] = 0

    # Cross-class dedupe: drop phishing URLs that also appear as legitimate
    legit_urls = set(legit_df["url"])
    overlap = phishing_df["url"].isin(legit_urls).sum()
    if overlap:
        print(
            f"[fetch_data] Dropping {overlap} phishing URLs that also appear "
            "in the legitimate set (cross-class duplicates)"
        )
    phishing_df = phishing_df[~phishing_df["url"].isin(legit_urls)]

    # Cap URLs per host in both classes (host-group downsampling)
    if max_per_host and max_per_host > 0:
        before_p, before_l = len(phishing_df), len(legit_df)
        phishing_df = _cap_per_host(phishing_df, max_per_host)
        legit_df = _cap_per_host(legit_df, max_per_host)
        print(
            f"[fetch_data] Host capping (max {max_per_host}/host): "
            f"phishing {before_p} -> {len(phishing_df)}, "
            f"legit {before_l} -> {len(legit_df)}"
        )

    combined = pd.concat([phishing_df, legit_df], ignore_index=True).sample(
        frac=1, random_state=42
    )
    out_path = Path(__file__).parent.parent / "data" / "processed" / "custom_dataset.csv"
    combined.to_csv(out_path, index=False)
    print(
        f"[fetch_data] Custom dataset: {len(combined)} URLs "
        f"({combined['label'].sum()} phishing, {(1 - combined['label']).sum()} legit) "
        f"-> {out_path}"
    )
    return combined


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def load_any_dataset(source: str = "uci", **kwargs) -> pd.DataFrame:
    """
    Load a dataset by name.

    source = "uci"         -> UCI Phishing Websites Dataset
    source = "custom"      -> PhishTank + Tranco custom dataset
    """
    source = source.lower()
    if source == "uci":
        return download_uci_dataset()
    elif source == "custom":
        return build_custom_dataset(**kwargs)
    else:
        raise ValueError(f"Unknown dataset source: {source}. Use 'uci' or 'custom'.")


if __name__ == "__main__":
    print("=== fetch_data.py ===")
    print("Usage:")
    print("  python -m src.fetch_data            # download UCI dataset")
    print("  python -m src.fetch_data --custom   # build PhishTank+Tranco+ealvaradob dataset")
    print()

    import argparse

    parser = argparse.ArgumentParser(description="Download/load phishing datasets")
    parser.add_argument(
        "--custom",
        action="store_true",
        help="Build custom PhishTank + Tranco dataset instead of UCI",
    )
    args = parser.parse_args()

    if args.custom:
        df = build_custom_dataset()
    else:
        df = download_uci_dataset()

    print(f"\nLoaded {len(df)} rows, {df.columns.tolist()}")
    print(df.head(3).to_string())
