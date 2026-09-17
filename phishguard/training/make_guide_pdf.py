#!/usr/bin/env python3
"""
make_guide_pdf.py - Generates "Phishing Detector Field Guide" PDF.

A teachable, entertaining study guide explaining the whole project:
code snippets, design rationale, CLI flags, evaluation numbers,
ethical considerations, viva Q&A and tooling advice.

Run:  .venv/bin/python make_guide_pdf.py
Out:  reports/Phishing_Detector_Field_Guide.pdf
"""

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE = Path(__file__).resolve().parent
OUT = BASE / "reports" / "Phishing_Detector_Field_Guide.pdf"

F = Path("/usr/share/fonts/TTF")
BODY = F / "DejaVuSans.ttf"
BODY_B = F / "DejaVuSans-Bold.ttf"
BODY_I = F / "DejaVuSans-Oblique.ttf"
BODY_BI = F / "DejaVuSans-BoldOblique.ttf"
MONO = F / "DejaVuSansMono.ttf"
MONO_B = F / "DejaVuSansMono-Bold.ttf"
MONO_I = F / "DejaVuSansMono-Oblique.ttf"

for pth in (BODY, BODY_B, BODY_I, BODY_BI, MONO, MONO_B, MONO_I):
    if not pth.exists():
        raise SystemExit(f"Missing font: {pth}")

INK = (24, 33, 51)
MUTED = (95, 108, 125)
NAVY = (20, 44, 84)
BLUE = (37, 99, 176)
GOLD = (196, 137, 22)
GREEN = (22, 130, 93)
RED = (178, 58, 58)
PAPER = (247, 245, 240)
CODE_BG = (15, 23, 42)
CODE_TX = (226, 232, 240)
CODE_CM = (122, 141, 163)
STORY_BG = (252, 246, 227)
STORY_BD = (214, 182, 108)

MARGIN = 18
PAGE_W = 210
PAGE_H = 297
USABLE = PAGE_W - 2 * MARGIN


class Guide(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font("DejaVu", "", str(BODY))
        self.add_font("DejaVu", "B", str(BODY_B))
        self.add_font("DejaVu", "I", str(BODY_I))
        self.add_font("DejaVu", "BI", str(BODY_BI))
        self.add_font("DejaVuMono", "", str(MONO))
        self.add_font("DejaVuMono", "B", str(MONO_B))
        self.add_font("DejaVuMono", "I", str(MONO_I))
        self.set_margins(MARGIN, 16, MARGIN)
        self.set_auto_page_break(True, margin=16)
        self.alias_nb_pages()
        self._chapter = ""

    # ---------- page furniture ----------
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(0, 6, self._chapter, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(210, 208, 200)
        self.set_line_width(0.2)
        self.line(MARGIN, 22, PAGE_W - MARGIN, 22)
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(0, 5, f"Phishing Detector - Field Guide   .   {self.page_no()}/{{nb}}", align="C")

    # ---------- helpers ----------
    def _ensure(self, h):
        if self.get_y() + h > PAGE_H - 18:
            self.add_page()

    def h1(self, num, title):
        self.add_page()
        self._chapter = f"{num}.  {title}"
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", 8)
        self.cell(9, 7, num, border=0, align="C", fill=True, new_x=XPos.RIGHT, new_y=YPos.NEXT)
        self.set_font("DejaVu", "B", 17)
        self.set_text_color(*INK)
        self.cell(0, 10, "  " + title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.9)
        self.line(MARGIN, self.get_y(), MARGIN + 34, self.get_y())
        self.ln(5)

    def h2(self, text):
        self._ensure(14)
        self.ln(1.5)
        self.set_font("DejaVu", "B", 12.5)
        self.set_text_color(*BLUE)
        self.cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(0.8)

    def h3(self, text):
        self._ensure(10)
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(*INK)
        self.cell(0, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def para(self, text, size=9.6, lh=5.2, color=INK, after=2.2):
        self.set_font("DejaVu", "", size)
        self.set_text_color(*color)
        self.multi_cell(0, lh, text, markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(after)

    def bullet(self, text, size=9.4, indent=3.5):
        self._ensure(7)
        self.set_font("DejaVu", "", size)
        self.set_text_color(*INK)
        x = self.get_x()
        self.set_fill_color(*GOLD)
        y = self.get_y() + 1.6
        self.rect(x + indent, y, 1.7, 1.7, "F")
        self.set_x(x + indent + 4)
        self.multi_cell(0, 4.9, text, markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def code(self, snippet, lang="", fs=7.7, lh=3.6):
        lines = snippet.strip("\n").split("\n")
        est_h = len(lines) * lh + 10
        if self.get_y() + est_h > PAGE_H - 18:
            self.add_page()
        if lang:
            self.set_font("DejaVu", "B", 6.4)
            self.set_text_color(*CODE_CM)
            self.cell(0, 4, "  " + lang.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        x0, y0 = self.get_x(), self.get_y()
        box_h = len(lines) * lh + 4
        self.set_fill_color(*CODE_BG)
        self.set_draw_color(50, 62, 84)
        self.set_line_width(0.25)
        self.rect(x0, y0, USABLE, box_h, "DF")
        self.set_xy(x0 + 3, y0 + 2)
        for ln in lines:
            self.set_x(x0 + 3)
            stripped = ln.lstrip()
            if stripped.startswith("#") or stripped.startswith("//"):
                self.set_text_color(*CODE_CM)
                self.set_font("DejaVuMono", "I", fs)
            elif stripped.startswith(">>>") or stripped.startswith("$ "):
                self.set_text_color(*GOLD)
                self.set_font("DejaVuMono", "B", fs)
            else:
                self.set_text_color(*CODE_TX)
                self.set_font("DejaVuMono", "", fs)
            self.cell(USABLE - 6, lh, ln[:110], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_xy(x0, y0 + box_h + 2.5)

    def story(self, label, text):
        # estimate height
        self.set_font("DejaVu", "", 9.2)
        n_lines = len(self.multi_cell(USABLE - 12, 4.7, text, dry_run=True, output="LINES"))
        h = n_lines * 4.7 + 9
        self._ensure(h + 3)
        x0, y0 = self.get_x(), self.get_y()
        self.set_fill_color(*STORY_BG)
        self.set_draw_color(*STORY_BD)
        self.set_line_width(0.3)
        self.rect(x0, y0, USABLE, h, "DF")
        self.set_font("DejaVu", "B", 7.2)
        self.set_text_color(*GOLD)
        self.set_xy(x0 + 4, y0 + 2.4)
        self.cell(0, 3.6, label)
        self.set_xy(x0 + 4, y0 + 6.8)
        self.set_font("DejaVu", "I", 9.2)
        self.set_text_color(*INK)
        self.multi_cell(USABLE - 9, 4.7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(y0 + h + 3)

    def table(self, headers, rows, widths, fs=8.4, aligns=None):
        n = len(headers)
        aligns = aligns or ["L"] * n
        est = (len(rows) + 1) * 7 + 4
        self._ensure(min(est, 60))
        self.set_font("DejaVu", "B", fs)
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        self.set_draw_color(210, 208, 200)
        self.set_line_width(0.2)
        for wdt, hdr in zip(widths, headers):
            self.cell(wdt, 6.4, " " + hdr, border=1, fill=True, align="L")
        self.ln()
        self.set_font("DejaVu", "", fs)
        self.set_text_color(*INK)
        fill = False
        LH = 3.9
        for row in rows:
            h = 6.0
            for wdt, cell_text in zip(widths, row):
                lines_n = len(self.multi_cell(wdt - 2, LH, str(cell_text), dry_run=True, output="LINES"))
                h = max(h, lines_n * LH + 2.4)
            if self.get_y() + h > PAGE_H - 18:
                self.add_page()
                self.set_font("DejaVu", "B", fs)
                self.set_fill_color(*NAVY)
                self.set_text_color(255, 255, 255)
                for wdt, hdr in zip(widths, headers):
                    self.cell(wdt, 6.4, " " + hdr, border=1, fill=True, align="L")
                self.ln()
                self.set_font("DejaVu", "", fs)
                self.set_text_color(*INK)
            x0, y0 = self.get_x(), self.get_y()
            self.set_fill_color(*(238, 241, 246) if fill else (255, 255, 255))
            for i, (wdt, cell_text, al) in enumerate(zip(widths, row, aligns)):
                self.set_xy(x0 + sum(widths[:i]), y0)
                self.multi_cell(wdt, LH, " " + str(cell_text), border=1, fill=fill, align=al)
            self.set_xy(x0, y0 + h)
            fill = not fill
        self.ln(2.5)


pdf = Guide()

# =====================================================================
# COVER
# =====================================================================
pdf.add_page()   # cover
pdf.set_fill_color(*NAVY)
pdf.rect(0, 0, PAGE_W, PAGE_H, "F")
pdf.set_fill_color(13, 27, 52)
pdf.rect(0, 0, PAGE_W, 60, "F")

pdf.set_y(46)
pdf.set_font("DejaVuMono", "B", 11)
pdf.set_text_color(*GOLD)
pdf.cell(0, 6, "  $ python src/check_url.py \"http://paypal.com.verify-login.ru\"", align="L")
pdf.ln(7)
pdf.set_font("DejaVuMono", "", 11)
pdf.set_text_color(140, 200, 160)
pdf.cell(0, 6, "  Verdict: PHISHING        p=0.705", align="L")

pdf.set_y(105)
pdf.set_font("DejaVu", "B", 34)
pdf.set_text_color(255, 255, 255)
pdf.cell(0, 14, "The Phishing Detector", align="C")
pdf.ln(15)
pdf.set_font("DejaVu", "B", 24)
pdf.set_text_color(*GOLD)
pdf.cell(0, 11, "Field Guide", align="C")

pdf.set_y(150)
pdf.set_font("DejaVu", "", 11.5)
pdf.set_text_color(190, 202, 220)
pdf.cell(0, 6, "How a 107,355-URL machine learning system was built,", align="C")
pdf.ln(6.5)
pdf.cell(0, 6, "why every design choice was made, and how to explain", align="C")
pdf.ln(6.5)
pdf.cell(0, 6, "all of it - code, flags, metrics, ethics - in your own words.", align="C")

pdf.set_y(216)
for i, (big, small) in enumerate([
    ("107,355", "real URLs trained on"),
    ("0.888", "RandomForest F1 - honest, not fake 1.0"),
    ("6 d.p.", "Python vs browser prediction parity"),
]):
    x = MARGIN + i * (USABLE / 3)
    pdf.set_xy(x, 216)
    pdf.set_font("DejaVu", "B", 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(USABLE / 3, 8, big, align="C")
    pdf.set_xy(x, 225)
    pdf.set_font("DejaVu", "", 7.8)
    pdf.set_text_color(160, 175, 198)
    pdf.cell(USABLE / 3, 10, small, align="C")

pdf.set_y(262)
pdf.set_font("DejaVu", "", 9)
pdf.set_text_color(130, 145, 170)
pdf.cell(0, 6, "Companion study guide to the phishing-detector project  .  AI Final Assignment", align="C")

# =====================================================================
# CHAPTER 1 - BIG PICTURE
# =====================================================================
pdf.h1("1", "The Big Picture")

pdf.para(
    "The project answers one question: **given only the text of a URL, is it a phishing link?** "
    "No network calls, no page content, no JavaScript - just the string. That constraint is deliberate: "
    "it makes the detector fast, private, and safe to demo (you never have to visit a live phishing page)."
)
pdf.code(
    "URL string\n"
    "   |\n"
    "   v\n"
    "features.py          extract_features(url) -> 18 numbers\n"
    "   |\n"
    "   +--> train.py      learn patterns from 107,355 labeled URLs\n"
    "   |        saves models/RandomForest.pkl (the brain)\n"
    "   |             models/LogisticRegression.pkl (the simple brain)\n"
    "   |\n"
    "   +--> check_url.py  CLI: load pipeline -> extract -> predict -> explain\n"
    "   |\n"
    "   +--> workspace/    the same 18 features + exported LR model in your browser",
    "pipeline",
)
pdf.h2("One extractor, three consumers")
pdf.para(
    "The single most important architectural decision: **one file defines the features, and everyone "
    "else imports it.** Training, the CLI, and the web app all compute the same 18 numbers from a URL. "
    "If training and inference disagreed even slightly, the model would be judging the world by rules "
    "it was never taught. We call this train/inference parity, and we test it to 6 decimal places."
)
pdf.h2("The cast of files")
pdf.table(
    ["File", "Role in one line"],
    [
        ["features.py", "The 18 feature functions - the vocabulary of the model"],
        ["features_test.py", "81 unit tests guarding each feature's behavior"],
        ["fetch_data.py", "Builds the dataset: downloads, dedupes, caps per host"],
        ["train.py", "Trains both models inside sklearn Pipelines, saves .pkl + reports"],
        ["evaluate.py", "Honest test-set scores, confusion matrix, ROC curve"],
        ["check_url.py", "The CLI: check any URL, explain the verdict"],
        ["export_model.py", "Optional: exports LR to JSON for the web demo (quarantined)"],
    ],
    [42, 138],
)
pdf.story(
    "IF YOU REMEMBER ONE THING",
    "A machine learning model is a function from features to a prediction. 90% of this project's bugs "
    "were feature- or data-bugs, not model bugs. The model only knows what the numbers tell it.",
)

# =====================================================================
# CHAPTER 2 - FEATURES
# =====================================================================
pdf.h1("2", "The 18 Features - Teaching a Machine to Be Suspicious")

pdf.para(
    "A URL is just text, so we convert it into 18 numbers describing its shape. Think of them as "
    "**suspicion instincts**: things a trained human notices in half a second without opening the link. "
    "The model's job is to learn which instincts matter and how much."
)
pdf.h2("The full vocabulary")
pdf.table(
    ["#", "Feature", "What it measures", "Why it helps"],
    [
        ["1", "url_length", "Total characters", "Phishing URLs are often long (padding to look real)"],
        ["2", "hostname_length", "Domain length", "Deceptive domains are wordy"],
        ["3", "path_length", "Length after the domain", "Deep fake login paths (verified by our data fix)"],
        ["4", "num_dots", "Dots in URL", "More labels = more places to hide the real domain"],
        ["5", "num_hyphens", "Hyphens", "secure-paypal-login.com energy"],
        ["6", "num_underscores", "Underscores", "Rare in honest URLs"],
        ["7", "num_slashes", "Slashes", "Deep nesting, often fake structure"],
        ["8", "num_digits", "Digit count", "Random junk domains love digits"],
        ["9", "num_special_chars", "@, %, =, &, ?...", "Obfuscation machinery"],
        ["10", "has_at_symbol", "Is @ present", "Classic trick: browser trusts what is BEFORE the @"],
        ["11", "has_ip_address", "Host is numbers", "No domain = no reputation = red flag"],
        ["12", "num_subdomains", "Labels before the TLD", "paypal.com.verify-login.ru has 3"],
        ["13", "uses_https", "Scheme is https", "Weak signal: phishers use https too now"],
        ["14", "has_https_token_in_path", "The word 'https' hiding in the path", "Faking security in text"],
        ["15", "is_shortened_url", "bit.ly, tinyurl...", "Hides the true destination"],
        ["16", "url_entropy", "Shannon entropy", "Random-looking strings score high"],
        ["17", "tld_in_subdomain", "A TLD name posing as a subdomain", "The homograph detector - see below"],
        ["18", "digit_letter_ratio", "Digits / letters", "More junk, more digits"],
    ],
    [7, 38, 62, 73],
    fs=7.6,
)

pdf.h2("Deep dive 1: the @ trick")
pdf.para(
    "In https://google.com@evil.ru/login the browser connects to **evil.ru** - everything before @ is "
    "decoration. Humans read left to right and get fooled; the feature has_at_symbol catches it instantly. "
    "One boolean, enormous historical signal."
)
pdf.h2("Deep dive 2: the bug that ate bbc.co.uk")
pdf.para(
    "Feature 17, tld_in_subdomain, was built to catch look-alike domains like "
    "**paypal.com.verify-login.ru** - the word .com hiding in the middle of the domain. "
    "The first version had an embarrassing bug:"
)
pdf.code(
    "# BEFORE - the naive version\n"
    "parts = hostname.split('.')\n"
    "if any(part in COMMON_TLDS for part in parts[:-1]):\n"
    "    return 1        # fires on bbc.co.uk  ('co' looks like a TLD!)\n"
    "\n"
    "# AFTER - with the ccTLD exemption\n"
    "for i, part in enumerate(parts[:-1]):\n"
    "    if part not in common_tlds:\n"
    "        continue\n"
    "    # 'co' in bbc.co.uk sits right before a 2-letter ccTLD:\n"
    "    # that is a legitimate multi-part suffix, not a trick\n"
    "    if i == len(parts) - 2 and len(final) == 2:\n"
    "        continue\n"
    "    return 1        # paypal.com.verify-login.ru still fires",
    "features.py (abridged)",
)
pdf.story(
    "WHY THIS BUG WAS DANGEROUS",
    "4.1% of legitimate URLs (bbc.co.uk, site.com.au style) were being flagged as suspicious. The false "
    "signal drowned the true one - the homograph paypal.com.verify-login.ru briefly scored as LEGITIMATE. "
    "The lesson: a feature bug is a model bug. We now test both bbc.co.uk (must NOT fire) and "
    "paypal.com.verify-login.ru (must fire) in features_test.py - 81 tests total.",
)
pdf.h2("Deep dive 3: shortened URLs")
pdf.para(
    "is_shortened_url checks the host against a list of shorteners (bit.ly, tinyurl.com, t.co, goo.gl, "
    "is.gd, cutt.ly and friends). Shorteners are not evil - but they are the standard cloak for phishing "
    "in messages, and the model learned to treat them as a strong signal (our smoke test: bit.ly link "
    "scores p=1.00)."
)

# =====================================================================
# CHAPTER 3 - DATA
# =====================================================================
pdf.h1("3", "The Data - Three Stories, Three Traps")

pdf.para(
    "The final dataset: **107,355 real URLs** - 48,338 phishing + 59,017 legitimate. But the road here "
    "taught more than the destination. Each source below fixed a real modeling disaster."
)
pdf.h2("The sources")
pdf.table(
    ["Source", "Class", "What it gives"],
    [
        ["PhishTank verified feed (online-valid.csv)", "phishing", "48k community-verified live phishing URLs"],
        ["Tranco top-10k list", "legitimate", "The 10,000 most-visited domains on Earth"],
        ["ealvaradob/phishing-dataset benign subset", "legitimate", "~59k real benign deep links WITH paths"],
        ["UCI Phishing Websites (id=327)", "benchmark only", "11k rows, 30 pre-computed features - NOT trained on"],
    ],
    [66, 26, 88],
    fs=8.0,
)
pdf.para(
    "Why not UCI for training? Its 30 features are pre-computed and anonymized - there are no raw URLs, "
    "so our feature extractor cannot run on it. Worse, several features (page_rank, web_traffic, "
    "google_index, dnsrecord, age_of_domain) need live network lookups, breaking the offline promise. "
    "It stays cached as a benchmark reference only.",
)

pdf.h2("Story 1: the perfect score that was a lie")
pdf.para(
    "The first dataset had 244 URLs - and the model scored F1 = 1.000. Perfect. Too perfect. "
    "The phishing URLs were mostly .ru and .xyz, the legitimate ones .com - the model could separate "
    "the classes **by top-level domain alone**. It was not learning phishing; it was learning our "
    "sampling habits. Rule of thumb: a perfect score on a small, hand-made dataset is a bug report, "
    "not a result."
)
pdf.h2("Story 2: any path = phishing (dataset bias)")
pdf.para(
    "Tranco only publishes bare homepages - google.com, never google.com/mail/u/0. PhishTank URLs "
    "usually have deep paths. So the model learned: **has a path = phishing.** It flagged "
    "github.com/python/cpython at 0.95. The fix was to add real benign URLs with paths, so both "
    "classes contain deep links:"
)
pdf.code(
    "# the bias, measured on the first dataset\n"
    "#   legit URLs containing a path :   0%   (Tranco = homepages only)\n"
    "#   phishing URLs with a path    :  61%   (PhishTank = deep links)\n"
    "# after adding ealvaradob benign URLs\n"
    "#   legit with paths : 77%   phishing with paths : 61%   -> no shortcut left",
    "dataset audit",
)
pdf.h2("Story 3: the docs.google.com memorization")
pdf.para(
    "PhishTank contained 5,700+ URLs all hosted on docs.google.com (abusing Google Forms for phishing). "
    "A random forest happily memorizes host-level patterns: '3 dots + short host = bad'. That inflates "
    "test scores but fails in the real world. Fix: **host capping**."
)
pdf.code(
    "def _cap_per_host(df, max_per_host):\n"
    "    \"\"\"Keep at most max_per_host URLs per hostname.\"\"\"\n"
    "    return (df.groupby(\"host\", group_keys=False)\n"
    "              .apply(lambda g: g.head(max_per_host)))\n"
    "\n"
    "# called for BOTH classes - fairness in capping:\n"
    "phishing_df = _cap_per_host(phishing_df, max_per_host)   # max 10/host\n"
    "legit_df    = _cap_per_host(legit_df,    max_per_host)",
    "fetch_data.py (abridged)",
)
pdf.h2("Hygiene: deduplication")
pdf.code(
    "# cross-class dedupe: if a URL is labeled BOTH ways, keep the benign one\n"
    "legit_urls = set(legit_df[\"url\"])\n"
    "overlap = phishing_df[\"url\"].isin(legit_urls).sum()\n"
    "phishing_df = phishing_df[~phishing_df[\"url\"].isin(legit_urls)]\n"
    "\n"
    "# plus exact dedupe per class; final shuffle with a fixed seed\n"
    "combined = pd.concat([...]).sample(frac=1, random_state=42)",
    "fetch_data.py (abridged)",
)
pdf.story(
    "THE SLEUTH'S SUMMARY",
    "Bias lives in how data is collected, not in the model. Tranco-only taught 'paths are evil'; "
    "PhishTank-heavy taught 'docs.google.com is evil'. Every fix made metrics WORSE (F1 0.9255 -> 0.888) "
    "and the system BETTER - because the dropped points were lies the data told.",
)

# =====================================================================
# CHAPTER 4 - THE PIPELINE FIX
# =====================================================================
pdf.h1("4", "The Pipeline Fix - One Scaler to Rule the Right Model")

pdf.h2("The bug")
pdf.para(
    "Version 1 fit ONE StandardScaler and fed scaled data to RandomForest AND LogisticRegression, then "
    "saved scaler.pkl separately for inference. Two problems: trees do not need scaling at all, and a "
    "loose scaler file is a **leakage and mismatch hazard** - any drift between training-time scaling "
    "and inference-time scaling silently corrupts predictions."
)
pdf.h2("The fix: preprocessing travels inside the model")
pdf.code(
    "lr_pipeline = Pipeline([\n"
    "    (\"scaler\", StandardScaler()),\n"
    "    (\"clf\", LogisticRegression(class_weight=\"balanced\",\n"
    "                               max_iter=1000, random_state=42)),\n"
    "])\n"
    "\n"
    "rf_pipeline = Pipeline([\n"
    "    (\"clf\", RandomForestClassifier(n_estimators=200,\n"
    "                                   class_weight=\"balanced\",\n"
    "                                   random_state=42, n_jobs=-1)),\n"
    "])   # no scaler - trees are scale-invariant\n"
    "\n"
    "joblib.dump(rf_pipeline, \"models/RandomForest.pkl\")   # ONE file each",
    "train.py (abridged)",
)
pdf.para(
    "Now the .pkl is **self-contained**: load it, hand it raw numbers, get a prediction. check_url.py "
    "shrank to three lines of inference: joblib.load, predict, predict_proba. And cross-validation "
    "becomes automatically honest: every CV fold refits the WHOLE pipeline, so the scaler is computed "
    "from that fold's training data only - **zero leakage**, with no extra code."
)
pdf.table(
    ["Question", "Answer to give in the viva"],
    [
        ["Why does LR need scaling?", "Its loss weighs features by magnitude; unscaled big-range features dominate"],
        ["Why doesn't RF need it?", "Trees split by thresholds per feature - scale never matters"],
        ["What is leakage?", "Test-set information sneaking into training (e.g. scaler fit on all data)"],
        ["How do we avoid it here?", "Pipeline + cross_val_score: every fold refits scaler + model from scratch"],
        ["What is class_weight=balanced?", "Re-weights classes inversely to frequency so minority errors hurt more"],
    ],
    [62, 118],
    fs=8.0,
)

# =====================================================================
# CHAPTER 5 - EVALUATION
# =====================================================================
pdf.h1("5", "Evaluation - Reading the Numbers Like an Adult")

pdf.h2("The headline results (test set = 21,471 URLs, stratified 80/20)")
pdf.table(
    ["Model", "Precision", "Recall", "F1", "ROC-AUC", "CV F1 (5-fold)"],
    [
        ["RandomForest", "0.8885", "0.8872", "0.8878", "0.9545", "0.8890 +/- 0.0023"],
        ["LogisticRegression", "0.8124", "0.7963", "0.8043", "0.8850", "0.8015 +/- 0.0033"],
    ],
    [38, 24, 24, 22, 24, 28],
    fs=8.0,
)
pdf.h2("What each metric actually says")
pdf.bullet("**Precision 0.8885** - when the model shouts PHISHING, it is right 88.9% of the time. Protects legitimate sites from being blocked.")
pdf.bullet("**Recall 0.8872** - of all real phishing, it catches 88.7%. The rest sail past; each miss is a potential victim.")
pdf.bullet("**F1 0.8878** - the harmonic mean; punishes imbalance between precision and recall. Our single headline number.")
pdf.bullet("**ROC-AUC 0.9545** - rank a random phish above a random legit URL 95.5% of the time. Measures separability across ALL thresholds.")
pdf.bullet("**CV F1 +/- std** - five retrainings on different splits land within 0.0023 of each other: the score is stable, not a lucky draw.")
pdf.h2("The confusion matrix, decoded (RandomForest)")
pdf.table(
    ["", "Predicted LEGIT", "Predicted PHISH"],
    [
        ["Actually LEGIT", "TN = 10,727 (correct pass)", "FP = 1,076 (false alarm)"],
        ["Actually PHISH", "FN = 1,091 (the misses)", "TP = 8,577 (caught)"],
    ],
    [40, 70, 70],
    fs=8.2,
)
pdf.para(
    "Read it as a story: of 9,803 real phishing attacks in the test set, the model catches 8,577 and "
    "misses 1,091; of 11,803 legitimate URLs it wrongly accuses 1,076. That FP/FN tension is the "
    "deployment tradeoff - and it is adjustable live with --threshold (Chapter 6)."
)
pdf.story(
    "WHY 0.888 IS THE HONEST NUMBER",
    "The brief expects F1 roughly in 0.85-0.97 on real data. Our 0.888 sits there because real phishing "
    "is genuinely hard: top phishing kits perfectly imitate real login pages, so pure URL shape has a "
    "ceiling. A perfect 1.0 on tiny data was the red flag; a stable 0.89 with tight CV variance is a "
    "result you can defend.",
)

# =====================================================================
# CHAPTER 6 - THE CLI
# =====================================================================
pdf.h1("6", "The CLI - check_url.py, Flag by Flag")

pdf.h2("The one-liner anatomy")
pdf.code(
    "$ python src/check_url.py <url> [--model NAME] [--threshold 0.5]\n"
    "                          [--json] [--list-models]",
    "usage",
)
pdf.table(
    ["Flag", "What it does inside the program"],
    [
        ["<url> (positional)", "The URL to judge. If the scheme is missing, http:// is assumed and a note is printed. No network call is EVER made - the string is only parsed."],
        ["--model NAME", "Which .pkl brain to load: RandomForest (default, 200 trees, ~53 MB) or LogisticRegression (2 KB, ~10 s faster startup, slightly lower accuracy)."],
        ["--threshold X", "Decision boundary, default 0.5. Lower = paranoid (more phishing calls, more false alarms); higher = only near-certain calls. Deployments tune this to taste."],
        ["--json", "Machine-readable output: verdict, probability, all 18 features, and the full contribution list. Perfect for piping into other tools or screenshots."],
        ["--list-models", "Lists every .pkl in models/ - a sanity check that training actually saved something."],
    ],
    [36, 144],
    fs=8.0,
)
pdf.h2("How a verdict is produced")
pdf.code(
    "pipeline = joblib.load(\"models/RandomForest.pkl\")   # scaler included\n"
    "feats = extract_features(url)                        # 18 numbers\n"
    "X = pd.DataFrame([feats], columns=get_feature_names())\n"
    "pred = pipeline.predict(X)[0]                        # 0 or 1\n"
    "prob = pipeline.predict_proba(X)[0, 1]               # p(phishing)\n"
    "pred = 1 if prob >= args.threshold else 0            # user's boundary",
    "check_url.py (the whole inference path)",
)
pdf.h2("The explain button - occlusion, explained")
pdf.para(
    "Global feature importances say what the model USUALLY cares about. They cannot explain a single "
    "verdict. So check_url.py runs a counterfactual experiment per URL: swap one feature to a "
    "benign-typical value, re-predict, and measure how much the probability moved:"
)
pdf.code(
    "for idx, name in enumerate(feature_names):\n"
    "    ref = _BENIGN_REFERENCE[name]      # e.g. has_at_symbol -> 0.0\n"
    "    Xc = X.copy()\n"
    "    Xc[0, idx] = float(ref)            # 'occlude' this feature\n"
    "    p = pipeline.predict_proba(Xc)[0, 1]\n"
    "    contribution = base_prob - p       # + pushed toward PHISHING\n",
    "check_url.py (abridged)",
)
pdf.code(
    "$ python src/check_url.py http://paypal.com.verify-login.ru/user/login\n"
    "Verdict: PHISHING        Phishing probability: 0.7050\n"
    "\n"
    "Top feature contributions (toward PHISHING + / toward LEGITIMATE -):\n"
    "  - num_subdomains = 3      -> +0.31   (the 'com' hiding in the middle)\n"
    "  - tld_in_subdomain = 1    -> +0.22   (the homograph rule fired)\n"
    "  - num_dots = 4            -> +0.09\n"
    "  - uses_https = 0          -> +0.04\n"
    "Benign baseline: 0.0340 - what the model would say if EVERY feature\n"
    "were typical of a legitimate URL.",
    "annotated example output",
)
pdf.h2("The import shim (a real-world papercut)")
pdf.para(
    "The modules use flat imports (from features import ...), which works when run as scripts but broke "
    "python -m src.check_url. The fix - try package imports first, fall back to flat - is a reusable "
    "pattern:"
)
pdf.code(
    "try:    # package mode:  python -m src.check_url\n"
    "    from .features import extract_features, get_feature_names\n"
    "except ImportError:   # script mode:  python src/check_url.py\n"
    "    from features import extract_features, get_feature_names",
    "dual-mode import",
)
pdf.story(
    "DEMO RECIPE FOR THE VIDEO",
    "Run these in order: www.google.com (legit), github.com/python/cpython (legit deep link), "
    "paypal.com.verify-login.ru (phish), bit.ly link (phish). Then rerun one with --threshold 0.3 to "
    "show the tradeoff, and finally --json to show the machine output. Sixty seconds, complete story.",
)

# =====================================================================
# CHAPTER 7 - WEB APP
# =====================================================================
pdf.h1("7", "The Web App - Same Brain, Different Body")

pdf.para(
    "A React + TypeScript demo (workspace/) runs the LogisticRegression model **in your browser, "
    "offline**. The LR pipeline is just arithmetic - z = bias + sum(w_i * (x_i - mean_i)/std_i), "
    "p = sigmoid(z) - so 2 KB of JSON reproduces it exactly. The 200-tree forest cannot be exported "
    "losslessly; the browser app runs LR and cites the Python CLI for RF."
)
pdf.h2("Proven parity")
pdf.code(
    "URL                              Python LR      Browser LR\n"
    "paypal.com.verify-login.ru/...   0.821943       0.821943\n"
    "bit.ly/3xY2zAb                   0.891398       0.891398\n"
    "www.google.com                   0.0004xx       0.0004xx   (all 10 test URLs match to 6 d.p.)",
    "parity test",
)
pdf.h2("The no-drift chain")
pdf.para(
    "Early on, the export had stale, hand-copied metrics - a maintenance trap. Now numbers flow one "
    "way only, with no human in the loop:"
)
pdf.code(
    "train.py finishes\n"
    "  -> writes reports/training_report.json (the single source of truth)\n"
    "  -> calls export_model.py automatically (best-effort, never fatal)\n"
    "       reads training_report.json LIVE - nothing is baked in\n"
    "       if the export is older than the .pkl files: loud STALE warning\n"
    "  -> writes workspace/src/model/lrModel.json (model + metrics)\n"
    "  -> web app derives ALL displayed numbers from that JSON",
    "sync architecture",
)
pdf.para(
    "**Scope note for the report:** the deliverable is the model + CLI; the web app is a clearly "
    "quarantined optional extra. Deleting export_model.py and workspace/ removes it with zero impact "
    "on the Python project."
)

# =====================================================================
# CHAPTER 8 - TRAPS PLAYBOOK
# =====================================================================
pdf.h1("8", "The Defensive-Engineering Playbook")

pdf.para(
    "Six traps this project fell into and climbed out of. Each is a story you can tell in the viva - "
    "graders love honest failure analysis more than fake perfection."
)
pdf.table(
    ["Trap", "Symptom", "Fix", "Lesson"],
    [
        ["Too-separable toy data", "F1 = 1.000 on 244 URLs", "Real sources: PhishTank + Tranco + ealvaradob", "Perfect scores on small data = sampling artifact"],
        ["Shared scaler file", "One scaler.pkl served two models", "Pipeline per model; scaler lives inside .pkl", "Preprocessing belongs to the model"],
        ["'Paths are evil' bias", "github deep links flagged 0.95", "Add benign URLs WITH paths (77% now)", "Balance shape, not just labels"],
        ["Host memorization", "5.7k docs.google.com URLs; host-pattern overfit", "Cap 10 URLs per host, both classes", "Cap sources, not classes"],
        ["Feature bug (ccTLD)", "bbc.co.uk flagged; homographs missed", "ccTLD exemption + regression tests", "A feature bug IS a model bug"],
        ["Export drift", "Stale metrics baked into JSON", "Auto-export after training; live report reads; stale alarm", "Single source of truth, zero hand-copied numbers"],
    ],
    [34, 42, 52, 52],
    fs=7.4,
)
pdf.story(
    "THE META-LESSON",
    "Every fix made the metrics worse and the system better. That inversion - dropping F1 from 0.9255 "
    "to 0.888 while deleting lies from the data - is the difference between optimizing a number and "
    "engineering a system.",
)

# =====================================================================
# CHAPTER 9 - ETHICS
# =====================================================================
pdf.h1("9", "Ethics, Limits, and Honest Failure Modes")

pdf.h2("Bias - inherited from the sources")
pdf.bullet("PhishTank skews toward campaign phishing (hosted kits, Google Forms abuse); Tranco/ealvaradob skew toward popular sites. Long-tail legitimate domains and novel phishing kits are underrepresented.")
pdf.bullet("Language and region bias: the sources skew toward English-language and Western URLs; TLD-heavy regions may see different error rates.")
pdf.h2("Misuse - how a detector becomes a weapon")
pdf.para(
    "An attacker can use the CLI as a free oracle to mutate a phishing URL until it scores LEGITIMATE - "
    "adversarial optimization. Mitigations in practice: rate-limit public scoring endpoints, combine "
    "lexical scores with content/reputation systems, and never rely on a single static model."
)
pdf.h2("False positives have victims too")
pdf.para(
    "A flagged legitimate URL can be blocked, costing businesses trust and money. That is why precision "
    "is reported as prominently as recall, and why --threshold exists: a bank's filter would set a "
    "higher bar; a mail provider a lower one."
)
pdf.h2("Hard limits of lexical-only detection")
pdf.bullet("Homoglyph IDN attacks (p\u0430ypal.com with a Cyrillic 'a') look almost normal as ASCII features.")
pdf.bullet("A clean-looking domain serving evil content passes - we never see the page.")
pdf.bullet("Novel TLD abuse (.zip, .mov style) can drift the feature distribution over time - models need periodic retraining on fresh feeds.")
pdf.h2("Mitigations, summarized")
pdf.bullet("Diverse sources + host capping + dedupe (done) - reduces the loudest biases.")
pdf.bullet("Documented limits (this chapter) - no overclaiming.")
pdf.bullet("Human in the loop - the tool ASSISTS judgment; it should not be the sole decision-maker.")
pdf.bullet("Scheduled retraining from live feeds - the pipeline (fetch -> train -> evaluate) is one command each.")

# =====================================================================
# CHAPTER 10 - VIVA CRAM
# =====================================================================
pdf.h1("10", "Viva Cram Sheet - Twelve Questions You Will Be Asked")

qa = [
    ("Why two models?",
     "RandomForest for accuracy (captures feature interactions, F1 0.888); LogisticRegression for "
     "transparency and portability (2 KB, exports to the browser). Comparing a complex and a simple "
     "model also shows whether complexity is earning its keep - it is (0.888 vs 0.804)."),
    ("Why not deep learning / neural networks?",
     "Tabular data of 18 engineered features is classic tree territory; a neural net would need more "
     "data, more compute, and would lose the per-feature explanations. Right tool for the right job."),
    ("Why is F1 not 1.0, and why is that GOOD?",
     "Because the data is real and the classes genuinely overlap - phishing kits imitate legitimate "
     "sites. The old 1.0 came from 244 URLs separable by TLD. Real, honest, defensible."),
    ("How do you prevent data leakage?",
     "Three layers: stratified split BEFORE any fitting; scaler inside the Pipeline so CV refits it "
     "per fold; cross-class URL deduplication so the same URL cannot sit in train and test with "
     "different labels."),
    ("What exactly is a sklearn Pipeline?",
     "A chained object of preprocessing steps + estimator that fits/predicts as one unit. It "
     "guarantees inference applies the exact same transforms as training, and makes the saved .pkl "
     "self-contained."),
    ("Why cap 10 URLs per host?",
     "PhishTank had 5,700+ URLs on docs.google.com. Without capping the forest memorizes host patterns "
     "instead of transferable lexical signals - high test scores, poor real-world generalization."),
    ("Why is Tranco not enough for the legit class?",
     "Tranco is bare homepages only - zero paths - while 61% of phishing has paths. The model learned "
     "'path = phishing'. The ealvaradob benign set (77% with paths) destroyed that shortcut."),
    ("What is the occlusion explanation?",
     "For THIS prediction: replace each feature with a benign-typical value one at a time, re-predict, "
     "and report the probability change. Positive = pushed toward phishing. Model-agnostic and "
     "intuitive; caveat: ignores feature interactions."),
    ("Why 18 hand-made features instead of the raw string?",
     "Interpretability and parity: every feature has a name, a test, and an explanation, and the same "
     "extractor runs in Python and JavaScript. Character-level models could score higher but explain less."),
    ("What does --threshold actually trade off?",
     "Recall vs precision. Threshold 0.3 catches more phishing at the cost of false alarms; 0.9 makes "
     "near-certain calls only. Deployment-specific: email filters favor recall, banking sites favor precision."),
    ("Biggest limitation?",
     "Lexical-only vision: we never see page content. Clean-domain-evil-content and homoglyph attacks "
     "slip through; the fix is pairing with content/reputation signals in production."),
    ("How would you improve it next?",
     "Scheduled retraining from fresh PhishTank pulls; host-reputation features; character n-gram or "
     "transformer URL models for the hard cases; calibration so probabilities mean frequencies."),
]
for i, (q, a) in enumerate(qa, 1):
    pdf._ensure(24)
    pdf.set_font("DejaVu", "B", 9.6)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 5, f"Q{i}. {q}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 9.3)
    pdf.set_text_color(*INK)
    pdf.multi_cell(0, 4.9, a, markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2.6)

# =====================================================================
# CHAPTER 11 - TOOLING
# =====================================================================
pdf.h1("11", "Tooling - What to Install and Why")

pdf.h2("JupyterLab: your lab notebook for the report")
pdf.para(
    "The report needs EDA screenshots and honest experimentation. JupyterLab inside the project venv "
    "is perfect for that: load custom_dataset.csv, plot class balance, test extract_features on your "
    "own URLs, and screenshot the outputs for the report's data section."
)
pdf.code(
    "# fish shell - inside the project folder\n"
    ".venv/bin/pip install jupyterlab ipykernel\n"
    "\n"
    "# register THIS venv as a named kernel (so notebooks use project deps)\n"
    ".venv/bin/python -m ipykernel install --user \\\n"
    "    --name phishing-detector --display-name \"Python (phishing-detector)\"\n"
    "\n"
    "# launch\n"
    ".venv/bin/jupyter lab",
    "terminal",
)
pdf.bullet("Notebook first cell: import pandas, load data/processed/custom_dataset.csv, df.label.value_counts() - screenshot that for the report.")
pdf.bullet("Keep canonical logic in src/ - notebooks are for exploration and evidence, not for the model code itself.")

pdf.h2("The rest of the submission toolbox")
pdf.table(
    ["Tool", "For", "Get it"],
    [
        ["LibreOffice Writer / MS Word", "The 5,000-word report (Times New Roman 12, 1.5 spacing)", "libreoffice.org or preinstalled"],
        ["LibreOffice Impress / PPT", "The presentation deck", "Same suite as above"],
        ["OBS Studio", "The 5-6 minute demo video (screen + mic)", "obsproject.com or flatpak"],
        ["Zotero", "Harvard-style references, in-text citations, bibliography", "zotero.org"],
        ["Peek / KOHA screenshots", "Screenshots of CLI output for the appendix", "Built-in screenshot tool is fine"],
    ],
    [48, 76, 56],
    fs=8.0,
)
pdf.story(
    "PRO TIP",
    "Record the terminal demo with the font enlarged (one URL per command, ~8 s each). Cut with any "
    "editor, add 30 s of slides for architecture and metrics, and your 5-6 minute video is done - "
    "script it from the Demo Recipe box in Chapter 6.",
)

# =====================================================================
# CHAPTER 12 - REPRODUCE
# =====================================================================
pdf.h1("12", "Reproduce Everything From Scratch")

pdf.code(
    "# 0. environment (fish shell)\n"
    "cd ~/Documents/AI/phishing-detector\n"
    "source .venv/bin/activate.fish\n"
    "\n"
    "# 1. data - raw caches live in data/raw/; --custom rebuilds the dataset\n"
    "python -m src.fetch_data --custom        # -> data/processed/custom_dataset.csv\n"
    "\n"
    "# 2. train (also refreshes the web export automatically)\n"
    "python -m src.train                      # -> models/*.pkl + reports/\n"
    "\n"
    "# 3. evaluate - metrics.json, confusion_matrix.png, roc_curve.png\n"
    "python -m src.evaluate\n"
    "\n"
    "# 4. test the features\n"
    "python src/features_test.py              # 81/81\n"
    "\n"
    "# 5. use it\n"
    "python src/check_url.py https://www.google.com\n"
    "python src/check_url.py http://paypal.com.verify-login.ru --json\n"
    "\n"
    "# 6. web demo (optional)\n"
    "cd ../workspace && npm install && npm run dev   # http://localhost:3000",
    "full pipeline",
)
pdf.h2("Where the evidence lives")
pdf.table(
    ["Artifact", "Meaning"],
    [
        ["reports/metrics.json + training_report.json", "The real test-set numbers; single source of truth"],
        ["reports/confusion_matrix.png / roc_curve.png", "Visuals to paste into the report"],
        ["reports/evaluation_summary.md", "Written analysis incl. ethics discussion"],
        ["models/RandomForest.pkl (53 MB, compressed)", "200 trees; identical predictions, 5.2x smaller file"],
        ["data/raw/ (gitignored)", "Regenerable caches - the code rebuilds them"],
    ],
    [76, 104],
    fs=8.0,
)
pdf.ln(2)
pdf.set_draw_color(*GOLD)
pdf.set_line_width(0.9)
pdf.line(MARGIN, pdf.get_y(), MARGIN + 34, pdf.get_y())
pdf.ln(4)
pdf.set_font("DejaVu", "I", 10.5)
pdf.set_text_color(*NAVY)
pdf.multi_cell(
    0, 5.6,
    "Final thought: the model is a mirror of its data. We spent more effort policing the data and the "
    "pipeline than tuning the model - and that is exactly why the numbers can be trusted.",
)

OUT.parent.mkdir(parents=True, exist_ok=True)
pdf.output(str(OUT))
print(f"OK -> {OUT}  ({OUT.stat().st_size/1e6:.1f} MB, {pdf.page_no()} pages)")
