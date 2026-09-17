#!/usr/bin/env python3
"""
make_model_choice_pdf.py - Generates "Why These Models?" PDF.

A short, plain-language explanation of PhishGuard's model-technology
choices: what LogisticRegression and RandomForest actually are, why each
was picked, what we compared them against, and how the decision was made.

Run:  python3 make_model_choice_pdf.py     (no venv needed - pure fpdf2)
Out:  reports/Model_Choice_Explained.pdf
"""

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE = Path(__file__).resolve().parent
OUT = BASE / "reports" / "Model_Choice_Explained.pdf"

F = Path("/usr/share/fonts/TTF")
BODY = F / "DejaVuSans.ttf"
BODY_B = F / "DejaVuSans-Bold.ttf"
BODY_I = F / "DejaVuSans-Oblique.ttf"
BODY_BI = F / "DejaVuSans-BoldOblique.ttf"
MONO = F / "DejaVuSansMono.ttf"

for pth in (BODY, BODY_B, BODY_I, BODY_BI, MONO):
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
BOX_BG = (252, 246, 227)
BOX_BD = (214, 182, 108)
CODE_BG = (15, 23, 42)
CODE_TX = (226, 232, 240)

MARGIN = 18
PAGE_W = 210
USABLE = PAGE_W - 2 * MARGIN


class Guide(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font("DejaVu", "", str(BODY))
        self.add_font("DejaVu", "B", str(BODY_B))
        self.add_font("DejaVu", "I", str(BODY_I))
        self.add_font("DejaVu", "BI", str(BODY_BI))
        self.add_font("Mono", "", str(MONO))
        self.set_auto_page_break(auto=True, margin=MARGIN)
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self._section = ""

    # ---- page furniture -------------------------------------------------
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "PhishGuard - Why These Models?", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        self.set_draw_color(*BOX_BD)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-14)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"Page {self.page_no()} of {{nb}}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # ---- building blocks -------------------------------------------------
    def h1(self, text):
        self.ln(2)
        self.set_font("DejaVu", "B", 22)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 9, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def h2(self, text):
        self.ln(3)
        self.set_font("DejaVu", "B", 13.5)
        self.set_text_color(*BLUE)
        self.multi_cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def body(self, text):
        self.set_font("DejaVu", "", 10.5)
        self.set_text_color(*INK)
        self.multi_cell(0, 5.6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.6)

    def bullet(self, label, text, color=INK):
        self.set_font("DejaVu", "B", 10.5)
        self.set_text_color(*color)
        self.cell(6, 5.6, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.cell(0 if not label else self.get_string_width(label) + 2, 5.6, label, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("DejaVu", "", 10.5)
        self.set_text_color(*INK)
        self.multi_cell(0, 5.6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.0)

    def callout(self, title, text):
        self.set_fill_color(*BOX_BG)
        self.set_draw_color(*BOX_BD)
        self.set_line_width(0.4)
        self.set_font("DejaVu", "BI", 10.5)
        self.set_text_color(*NAVY)
        x, y = self.get_x(), self.get_y()
        self.multi_cell(0, 5.6, f"{title}\n{text}", border=1, fill=True, padding=(4, 3, 4, 3), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def code(self, lines):
        self.set_font("Mono", "", 8.6)
        self.set_fill_color(*CODE_BG)
        self.set_text_color(*CODE_TX)
        self.multi_cell(0, 4.6, "\n".join(lines), fill=True, padding=(4, 3, 4, 3), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def metrics_table(self, rows, widths=(52, 30, 30, 46)):
        hdr = ("Model", "F1", "ROC-AUC", "Speed (per URL)")
        self.set_font("DejaVu", "B", 9.5)
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        for w, h in zip(widths, hdr):
            self.cell(w, 7, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("DejaVu", "", 9.5)
        self.set_text_color(*INK)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(240, 238, 232)
            for w, val in zip(widths, row):
                self.cell(w, 7, val, border=1, fill=fill, align="C")
            self.ln()
            fill = not fill
        self.ln(2)


pdf = Guide()
pdf.add_page()

# ======================================================================
# Cover / intro
# ======================================================================
pdf.h1("Why These Models?")
pdf.set_font("DejaVu", "I", 11)
pdf.set_text_color(*MUTED)
pdf.multi_cell(0, 5.6, "A plain-language walkthrough of how PhishGuard picks its brain.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(2)
pdf.body(
    "PhishGuard's job: look at a URL and say whether it's a phishing link - WITHOUT visiting the "
    "website. It only reads the address itself (length, weird subdomains, '@' tricks, entropy, and so "
    "on). That means the model has to learn from 18 simple numbers per URL. Two models do this job in "
    "this project: LogisticRegression and RandomForest. Here's why each one is there."
)

# ======================================================================
# The candidates
# ======================================================================
pdf.h2("The two models, in one sentence each")
pdf.bullet("LogisticRegression (LR): ", "adds up weighted clues and squashes the total into a 0-100% phishing score. Simple, fast, and you can read exactly why it decided anything.")
pdf.bullet("RandomForest (RF): ", "asks 200 simpler 'decision trees' to vote. Each tree sees a random slice of the data; the majority wins. Stronger, but a tangle of thousands of rules.")

pdf.h2("What we measured (21,471 held-out real URLs)")
pdf.metrics_table([
    ("RandomForest", "0.888", "0.954", "slow (~20 s load)"),
    ("LogisticRegression", "0.804", "0.885", "instant (~0.3 s)"),
])
pdf.body(
    "RF wins on paper. So why does the website run LR? Because the two products have different jobs - "
    "and that distinction drives everything below."
)

# ======================================================================
# Why LR runs the site
# ======================================================================
pdf.add_page()
pdf.h2("Decision 1 - the website runs LogisticRegression")
pdf.body("The site must run inside your browser, with no server. That means the model has to be exported as plain data. The two models are wildly different in how easy that is:")
pdf.bullet("LR is just arithmetic: ", "a list of 18 weights, one bias, and the formula score = sigmoid(bias + sum(weight x feature)). That fits in a ~2 KB JSON file, and a browser reproduces Python's answers EXACTLY - same math, digit for digit.")
pdf.bullet("RF is a library: ", "200 trees with thousands of branching rules can't be translated to the browser without either rebuilding all of sklearn in JavaScript or shipping a 53 MB blob. Not practical.")
pdf.body(
    "And the twist that makes it a fair trade: the small accuracy gap mostly reflects harder examples, "
    "not a broken model. LR still catches what URLs look like when they're fishy - and the site shows "
    "you exactly which features pushed its verdict, with real numbers."
)
pdf.callout(
    "The trade in one line:",
    "We gave up ~8 points of F1 to gain exact reproducibility, instant startup, and per-verdict explanations in the browser.",
)

# ======================================================================
# Why RF exists at all
# ======================================================================
pdf.h2("Decision 2 - RandomForest stays as the accuracy benchmark")
pdf.body(
    "If LR were hopelessly weak, the trade above would be dishonest. RF answers that question. It is "
    "trained and evaluated on exactly the same data and features, and its higher F1 (0.888 vs 0.804) "
    "proves the 18 features carry real signal that a stronger learner can exploit. It also gives the "
    "Results page its two most useful pictures: the confusion matrix and the feature-importance ranking "
    "(hostname length, path length, entropy...). In short: LR is the product, RF is the ceiling."
)

# ======================================================================
# Why not the others
# ======================================================================
pdf.h2("Decision 3 - why not XGBoost, a neural net, or k-NN?")
pdf.bullet("Gradient boosting (XGBoost/LightGBM): ", "usually the top scorer on tables like this - but it adds a heavy dependency and would ALSO be stuck in Python with the same export problem as RF. All cost, no product benefit over RF.")
pdf.bullet("Neural network: ", "shines on raw text, images, or audio. Here the inputs are already 18 tidy numbers; a neural net would be a bigger, opaque version of LR with the same job. Overkill.")
pdf.bullet("k-NN / Naive Bayes / SVM: ", "kept as honest baselines during development - but each loses to LR+RF on some axis that matters (speed, exportability, or accuracy), so none earned a place.")

# ======================================================================
# The data
# ======================================================================
pdf.add_page()
pdf.h2("Decision 4 - train on 107,355 real URLs, not toy data")
pdf.body("An early run on a 244-URL toy dataset scored a suspicious F1 of 1.000 - the classes were trivially separable by top-level domain. The fix was the dataset, not the model:")
pdf.bullet("Phishing: ", "48,338 verified URLs from the PhishTank feed.")
pdf.bullet("Legitimate: ", "Tranco top-10k domains PLUS real deep links, so both classes contain URLs with paths - otherwise the model learns 'has a path = phishing', which is dataset bias, not knowledge.")
pdf.bullet("Hygiene: ", "dedupe everything, and cap any single host at 10 URLs so the model learns transferable patterns instead of memorizing hosts.")

pdf.h2("Decision 5 - recall over precision")
pdf.body(
    "The two errors are not equal: flagging a good URL is annoying; missing a phishing link can cost "
    "someone their password. Training used class_weight='balanced' to punish missed phishing harder, "
    "and the threshold is adjustable. That bias is deliberate and disclosed on the site's Methodology tab."
)

pdf.h2("The decision process, step by step")
pdf.code([
    "1. Start simple: LR baseline + RF benchmark, same data, same features",
    "2. Measure: 5-fold CV + a 21,471-URL test set both models never saw",
    "3. Check honesty: CV F1 ~= test F1 for both  ->  no fluke, no leakage",
    "4. Ask the product question: where must the model RUN?",
    "5. Browser + exact parity + explanations  ->  LR ships, RF benchmarks",
])

pdf.callout(
    "If you remember one thing:",
    "Model choice = accuracy x deployability x explainability. RF is the most accurate, LR is the most deployable and explainable - so PhishGuard ships LR to your browser and keeps RF as the proof the features work.",
)

pdf.h2("Numbers cheat-sheet")
pdf.metrics_table([
    ("RandomForest", "0.888", "0.954", "CLI / benchmark"),
    ("LogisticRegression", "0.804", "0.885", "website (in-browser)"),
], widths=(52, 30, 30, 46))
pdf.set_font("DejaVu", "I", 9)
pdf.set_text_color(*MUTED)
pdf.multi_cell(0, 5, "Both trained on 107,355 real URLs, 80/20 stratified split, 5-fold cross-validation. "
                     "Verdict threshold 0.5. Regenerate anytime: python -m src.train (in training/).",
               new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.output(str(OUT))
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, {pdf.page_no()} pages)")
