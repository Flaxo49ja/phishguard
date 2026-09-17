# PhishGuard Consolidation & Site Remake — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the split project into one `phishguard/` folder (site-first: `web/` + `training/`) and remake the dark security-console UI.

**Architecture:** Static React+Vite+TS+Tailwind site running the exported LogisticRegression pipeline JSON in the browser (exact Python parity); Python training pipeline moved unchanged into `training/` with only the export path updated.

**Tech Stack:** React 18, TypeScript 5, Vite 6, Tailwind CSS 4, vitest 5; Python 3.11+/scikit-learn (training only).

**Spec:** `docs/superpowers/specs/2026-09-17-phishguard-consolidation-design.md`

## Global Constraints

- Feature extraction semantics must NOT change (Python ↔ TS parity).
- Model JSON files must be copied byte-identical (no re-export).
- Old `workspace/` and `phishing-detector/` directories are removed after successful moves.
- UI language: English; dark security-console aesthetic (slate-950, red→orange gradients, glass cards).
- Tests: vitest in `web/` (`npm test` = `vitest run`), typecheck `tsc --noEmit`, build `vite build`.

---

### Task 1: Scaffold `phishguard/` and move `training/`

**Files:**
- Create: root `.gitignore` (project root has NO git repo yet — we init one)
- Create: `phishguard/.gitignore`, `phishguard/README.md` (placeholder, finalized in Task 6)
- Move: `phishing-detector/` → `phishguard/training/`
- Modify: `phishguard/training/src/export_model.py` (WEB_SRC path)
- Modify: `phishguard/training/README.md` (path references)

- [ ] **Step 0: Init git repo at project root (none exists) and ignore the big zip**

```bash
git init
printf 'AI-project.zip\n' > .gitignore
```

(The 54 MB `AI-project.zip` must never be committed; `phishguard/.gitignore` in Step 4 covers its own subtree.)

- [ ] **Step 1: Create folder and move training pipeline**

```bash
mkdir -p phishguard
mv phishing-detector phishguard/training
rm -rf phishguard/training/.venv
```

- [ ] **Step 2: Update export_model.py output path**

In `phishguard/training/src/export_model.py` replace:

```python
WEB_SRC = BASE_DIR.parent / "workspace" / "src"
```

with:

```python
WEB_SRC = BASE_DIR.parent / "web" / "src"
```

Also update the two docstring mentions of `../workspace/` to `../web/` and the note "delete this file and ../workspace/" accordingly.

- [ ] **Step 3: Patch README paths inside training/**

In `phishguard/training/README.md`:
- Replace `../workspace/` with `../web/` (multiple occurrences).
- Replace section header "## Demo Video" stays; CLI examples stay valid (`python src/check_url.py ...` — relative paths unaffected).
- Add one line at the top: `> This folder is the training pipeline for the PhishGuard site in ../web/.`

- [ ] **Step 4: Write merged .gitignore**

Create `phishguard/.gitignore`:

```gitignore
# Python
__pycache__/
*.pyc
.venv/

# Regenerable raw downloads
training/data/raw/*.csv
training/data/raw/*.json

# Node
node_modules/
dist/
build/
*.log

# OS / editor
.DS_Store
```

- [ ] **Step 5: Verify the move**

```bash
ls phishguard/training/src/check_url.py && ls phishguard/training/models/lr_fast.json
```

Expected: both files exist; `phishing-detector/` and `workspace/` still present.

- [ ] **Step 6: Commit**

```bash
git add -A phishguard docs
git commit -m "chore: move python training pipeline into phishguard/training"
```

---

### Task 2: Scaffold `phishguard/web/` from workspace/ (clean)

**Files:**
- Move: `workspace/index.html`, `workspace/package.json`, `workspace/vite.config.js`, `workspace/tsconfig.json` → `phishguard/web/`
- Move: `workspace/src/features.ts`, `workspace/src/modelLoader.ts`, `workspace/src/classifier.ts`, `workspace/src/sampleUrls.ts`, `workspace/src/main.tsx` → `phishguard/web/src/`
- Move: `workspace/src/model/` → `phishguard/web/src/model/`
- Create: `phishguard/web/src/App.tsx` (slim shell, this task)
- Create: `phishguard/web/src/index.css` (Tailwind import + small utilities)
- Create: `phishguard/web/src/components/` (empty dir placeholder via .gitkeep)

- [ ] **Step 1: Move web files**

```bash
mkdir -p phishguard/web/src/components phishguard/web/src/lib
git rm -r --cached workspace 2>/dev/null || true
mv workspace/index.html workspace/package.json workspace/vite.config.js workspace/tsconfig.json phishguard/web/
mv workspace/src/features.ts workspace/src/modelLoader.ts workspace/src/classifier.ts workspace/src/sampleUrls.ts workspace/src/main.tsx phishguard/web/src/
mv workspace/src/model phishguard/web/src/model
```

- [ ] **Step 2: Clean index.html**

Replace the whole file with:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="PhishGuard — machine-learning phishing URL detector that runs entirely in your browser." />
    <title>PhishGuard — ML Phishing URL Detector</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Update package.json**

Set name to `phishguard-web`, move `vitest` to devDependencies `scripts.test`, keep versions identical:

```json
{
  "name": "phishguard-web",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "typecheck": "tsc --noEmit",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.1.7",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.3.4",
    "tailwindcss": "^4.1.7",
    "typescript": "^5.7.0",
    "vite": "^6.3.5",
    "vitest": "^5.0.0"
  }
}
```

- [ ] **Step 4: Move lib files into lib/ and fix imports**

```bash
mv phishguard/web/src/features.ts phishguard/web/src/modelLoader.ts phishguard/web/src/classifier.ts phishguard/web/src/sampleUrls.ts phishguard/web/src/lib/
```

Import-path fixes inside `lib/`:
- `modelLoader.ts`: `from './model/lrModel.json'` → `from '../model/lrModel.json'` (same for rfFeatureImportances) and `from './features'` → `from './features'` (both in lib/, unchanged).
- `classifier.ts`: no change needed (imports all from `./` siblings).

- [ ] **Step 5: Write index.css**

```css
@import "tailwindcss";

@theme {
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

html {
  scroll-behavior: smooth;
}

body {
  background-color: #020617;
  color: #e2e8f0;
}

/* Animated entrance for cards/results */
@keyframes rise-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-rise {
  animation: rise-in 0.35s ease-out both;
}

@keyframes bar-grow {
  from { width: 0; }
}
.animate-bar {
  animation: bar-grow 0.8s ease-out both;
}
```

- [ ] **Step 6: Write minimal App.tsx shell (compiles now, sections filled in Task 3-5)**

```tsx
import { useState } from 'react';

type TabType = 'checker' | 'methodology' | 'features' | 'results';

export default function App() {
  const [activeTab] = useState<TabType>('checker');
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto max-w-7xl px-4 py-8">
        <p className="text-slate-400">Shell — sections land in Tasks 3–5.</p>
      </main>
    </div>
  );
}
```

Note: main.tsx already imports `./index.css` and `./App.tsx` — paths still valid.

- [ ] **Step 7: Delete workspace/ (drop its .git, approved)**

```bash
rm -rf workspace
```

- [ ] **Step 8: Install & verify**

```bash
cd phishguard/web && npm install && npm run typecheck && npm run build
```

Expected: typecheck passes, build emits dist/.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat(web): scaffold phishguard/web from workspace, clean shell"
```

---

### Task 3: Golden-master parity tests (vitest)

**Files:**
- Create: `phishguard/web/src/lib/check_url_golden.json` (copied byte-identical from `phishguard/training/src/check_url_golden.json`)
- Create: `phishguard/web/src/lib/features.test.ts`
- Create: `phishguard/web/src/lib/classifier.test.ts`

**Interfaces:**
- Consumes: `extractFeatures(url: string): Record<string, number | boolean>` from `./features`; `classifyUrl(url: string): ClassificationResult` from `./classifier` (verdict, probability, allFeatures, benignBaselineProbability); `predictWithRealModel` internals via classifier output.
- Produces: regression guard for Tasks 4–5 refactors (must stay green).

- [ ] **Step 1: Copy golden fixture**

```bash
cp phishguard/training/src/check_url_golden.json phishguard/web/src/lib/check_url_golden.json
```

- [ ] **Step 2: Write features.test.ts**

```ts
import { describe, it, expect } from 'vitest';
import { extractFeatures, urlEntropy, hasIpAddress, tldInSubdomain } from './features';

describe('extractFeatures — python parity', () => {
  it('google.com: bare homepage shape', () => {
    const f = extractFeatures('https://www.google.com');
    expect(f.url_length).toBe(22);
    expect(f.hostname_length).toBe(14);
    expect(f.path_length).toBe(0);
    expect(f.num_dots).toBe(2);
    expect(f.num_subdomains).toBe(1);
    expect(f.uses_https).toBe(true);
    expect(f.url_entropy).toBe(3.6635);
  });

  it('no scheme: prepends http:// like the CLI', () => {
    const f = extractFeatures('bit.ly/3xample');
    expect(f.url_length).toBe(21);
    expect(f.is_shortened_url).toBe(true);
    expect(f.uses_https).toBe(false);
  });

  it('@ handling: hostname is after the LAST @', () => {
    const f = extractFeatures('http://user@legitimate-looking.com@phishing-site.net');
    expect(f.hostname_length).toBe(17); // phishing-site.net
    expect(f.has_at_symbol).toBe(true);
  });

  it('ccTLD exemption: bbc.co.uk does not fire tld_in_subdomain', () => {
    expect(tldInSubdomain('www.bbc.co.uk')).toBe(false);
  });

  it('tld_in_subdomain fires on paypal.com.evil.ru', () => {
    expect(tldInSubdomain('paypal.com.evil.ru')).toBe(true);
  });

  it('raw IPv4 hostname detected with octet validation', () => {
    expect(hasIpAddress('192.168.1.1')).toBe(true);
    expect(hasIpAddress('999.1.1.1')).toBe(false);
    expect(hasIpAddress('example.com')).toBe(false);
  });

  it('entropy matches python rounding to 4 decimals', () => {
    expect(urlEntropy('https://www.google.com')).toBe(3.6635);
  });

  it('digit_letter_ratio is 0 when no letters', () => {
    const f = extractFeatures('http://192.168.1.1');
    expect(f.digit_letter_ratio).toBe(0);
  });
});
```

- [ ] **Step 3: Run tests, expect green (they pin current behavior)**

```bash
cd phishguard/web && npm test
```

Expected: all pass (parity already holds — these are guards, not TDD-new behavior).

- [ ] **Step 4: Write classifier.test.ts (golden master)**

```ts
import { describe, it, expect } from 'vitest';
import golden from './check_url_golden.json';
import { classifyUrl } from './classifier';

interface GoldenEntry {
  raw_input: string;
  response: {
    url: string;
    verdict: string;
    phishing_probability: number;
    features: Record<string, number>;
    benign_baseline_probability: number;
  };
}

const entries = golden as GoldenEntry[];

describe('classifier — golden master parity with Python CLI', () => {
  it.each(entries)('$raw_input', ({ raw_input, response }) => {
    const result = classifyUrl(raw_input);
    expect(result.probability).toBeCloseTo(response.phishing_probability, 3);
    expect(result.verdict).toBe(response.verdict);
    expect(result.benignBaselineProbability).toBeCloseTo(response.benign_baseline_probability, 3);
    for (const [name, value] of Object.entries(response.features)) {
      const actual = result.allFeatures[name]?.value;
      const normalized = typeof actual === 'boolean' ? (actual ? 1 : 0) : actual;
      expect(normalized).toBe(value);
    }
  });
});
```

Note: golden fixture holds the CLI's own classification threshold behavior; the web classifier uses the same 0.5 threshold, so verdicts must match exactly.

- [ ] **Step 5: Run full web test suite**

```bash
cd phishguard/web && npm test
```

Expected: 16+ tests pass (8 feature cases + 8 golden entries).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "test(web): golden-master parity tests against python CLI outputs"
```

---

### Task 4: Components — Checker tab

**Files:**
- Create: `phishguard/web/src/components/UrlChecker.tsx`
- Create: `phishguard/web/src/components/VerdictCard.tsx`
- Create: `phishguard/web/src/components/ContributionList.tsx`
- Create: `phishguard/web/src/components/FeatureGrid.tsx`
- Create: `phishguard/web/src/components/SampleUrls.tsx`
- Create: `phishguard/web/src/components/HistoryList.tsx`
- Modify: `phishguard/web/src/App.tsx` (render Checker tab)

**Interfaces:**
- Consumes: `classifyUrl`, `isValidUrl`, `SAMPLE_URLS`, `ClassificationResult` from `../lib/classifier`; `FEATURE_DESCRIPTIONS` from `../lib/features`.
- Produces: `UrlChecker` (self-contained: input, verdict, contributions, samples, history). `VerdictCard({ result }: { result: AnalysisResult })`, `ContributionList({ result })`, `FeatureGrid({ result })`, `SampleUrls({ onPick })`, `HistoryList({ history, onSelect })` — `AnalysisResult = ClassificationResult & { url: string; timestamp: Date }` defined in `UrlChecker.tsx` and imported by siblings.

- [ ] **Step 1: Write UrlChecker.tsx (state owner)**

```tsx
import { useCallback, useState } from 'react';
import { classifyUrl, isValidUrl, SAMPLE_URLS } from '../lib/classifier';
import type { ClassificationResult } from '../lib/classifier';
import VerdictCard from './VerdictCard';
import ContributionList from './ContributionList';
import FeatureGrid from './FeatureGrid';
import SampleUrls from './SampleUrls';
import HistoryList from './HistoryList';

export interface AnalysisResult extends ClassificationResult {
  url: string;
  timestamp: Date;
}

export default function UrlChecker() {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>([]);

  const analyze = useCallback((input?: string) => {
    const target = (input ?? url).trim();
    if (!target) { setError('Enter a URL to analyze.'); return; }
    if (!isValidUrl(target)) { setError('Enter a valid URL, e.g. https://example.com'); return; }
    setError('');
    const analysis: AnalysisResult = { ...classifyUrl(target), url: target, timestamp: new Date() };
    setResult(analysis);
    setHistory((prev) => [analysis, ...prev].slice(0, 10));
  }, [url]);

  const selectHistory = (item: AnalysisResult) => { setUrl(item.url); setResult(item); };

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="space-y-3 py-6 text-center">
        <h2 className="bg-gradient-to-r from-red-400 via-orange-400 to-amber-300 bg-clip-text text-3xl font-bold text-transparent md:text-5xl">
          Is this URL safe to open?
        </h2>
        <p className="mx-auto max-w-2xl text-slate-400">
          A real machine-learning model — trained on 107,355 URLs — runs entirely in your browser.
          18 lexical features, zero network calls.
        </p>
      </div>

      {/* Input */}
      <div className="mx-auto max-w-3xl">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <label htmlFor="url-input" className="mb-2 block text-sm font-medium text-slate-300">
            URL to analyze
          </label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              id="url-input"
              type="text"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setError(''); }}
              onKeyDown={(e) => { if (e.key === 'Enter') analyze(); }}
              placeholder="https://example.com/login"
              className="w-full rounded-xl border border-white/10 bg-slate-900/80 px-4 py-3 font-mono text-sm text-slate-100 placeholder-slate-500 outline-none transition focus:border-orange-500/50 focus:ring-2 focus:ring-orange-500/30"
            />
            <button
              onClick={() => analyze()}
              className="shrink-0 rounded-xl bg-gradient-to-r from-red-500 to-orange-500 px-6 py-3 font-semibold text-white shadow-lg shadow-red-500/20 transition active:scale-95 hover:shadow-orange-500/40"
            >
              Analyze
            </button>
          </div>
          {error && <p className="mt-3 text-sm text-red-400" role="alert">{error}</p>}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="animate-rise mx-auto max-w-3xl space-y-4">
          <VerdictCard result={result} />
          <ContributionList result={result} />
          <FeatureGrid result={result} />
        </div>
      )}

      <SampleUrls onPick={analyze} />
      <HistoryList history={history.slice(1)} onSelect={selectHistory} />
    </div>
  );
}
```

- [ ] **Step 2: Write VerdictCard.tsx**

```tsx
import type { AnalysisResult } from './UrlChecker';

const verdictTheme = {
  PHISHING: {
    card: 'border-red-500/30 bg-red-950/40',
    icon: 'bg-red-500/15 text-red-400',
    text: 'text-red-400',
    bar: 'from-red-600 to-red-400',
  },
  LEGITIMATE: {
    card: 'border-emerald-500/30 bg-emerald-950/40',
    icon: 'bg-emerald-500/15 text-emerald-400',
    text: 'text-emerald-400',
    bar: 'from-emerald-600 to-emerald-400',
  },
} as const;

export default function VerdictCard({ result }: { result: AnalysisResult }) {
  const theme = verdictTheme[result.verdict];
  const pct = (result.probability * 100).toFixed(1);
  return (
    <div className={`animate-rise rounded-2xl border p-6 ${theme.card}`}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className={`flex h-12 w-12 items-center justify-center rounded-full text-2xl ${theme.icon}`}>
            {result.verdict === 'PHISHING' ? '⚠' : '✓'}
          </div>
          <div>
            <h3 className={`text-2xl font-bold ${theme.text}`}>{result.verdict}</h3>
            <p className="text-sm text-slate-400">
              Confidence: {result.confidence} · {(result.probability * 100).toFixed(1)}% phishing
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className={`font-mono text-3xl font-bold ${theme.text}`}>{pct}%</div>
        </div>
      </div>
      <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-800">
        <div className={`animate-bar h-full rounded-full bg-gradient-to-r ${theme.bar}`} style={{ width: `${result.probability * 100}%` }} />
      </div>
      <p className="mt-2 text-xs text-slate-500">
        Benign baseline: {(result.benignBaselineProbability * 100).toFixed(1)}% — what the model would predict if every feature looked benign-typical.
      </p>
      <div className="mt-4 rounded-xl border border-white/5 bg-slate-900/60 p-3">
        <div className="text-xs text-slate-500">Analyzed URL</div>
        <div className="break-all font-mono text-sm text-slate-300">{result.url}</div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write ContributionList.tsx**

```tsx
import type { AnalysisResult } from './UrlChecker';
import { FEATURE_DESCRIPTIONS } from '../lib/features';

export default function ContributionList({ result }: { result: AnalysisResult }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
      <h4 className="mb-4 font-semibold text-white">Why this verdict</h4>
      <div className="space-y-2.5">
        {result.topContributingFeatures.map((f) => {
          const phish = f.contribution >= 0;
          const width = Math.min(Math.abs(f.contribution) * 120, 100);
          return (
            <div key={f.feature} className="flex items-center gap-3">
              <div className="w-40 shrink-0">
                <div className="text-sm text-slate-200">{f.feature.replaceAll('_', ' ')}</div>
                <div className="text-xs text-slate-500">{FEATURE_DESCRIPTIONS[f.feature]}</div>
              </div>
              <div className="relative h-6 flex-1 overflow-hidden rounded-md bg-slate-800/60">
                <div className={`h-full ${phish ? 'ml-auto bg-gradient-to-l from-red-500/70' : 'bg-gradient-to-r from-emerald-500/70'}`} style={{ width: `${width}%` }} />
              </div>
              <div className="w-28 shrink-0 text-right">
                <span className={`font-mono text-xs ${phish ? 'text-red-400' : 'text-emerald-400'}`}>
                  {phish ? '+' : ''}{f.contribution.toFixed(4)}
                </span>
                <span className="ml-2 text-xs text-slate-500">{String(f.value)}</span>
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-xs text-slate-500">
        Occlusion: change in phishing probability when the feature is swapped to a benign-typical value. Positive = pushed toward phishing.
      </p>
    </div>
  );
}
```

- [ ] **Step 4: Write FeatureGrid.tsx**

```tsx
import { useState } from 'react';
import type { AnalysisResult } from './UrlChecker';

const riskColor = { high: 'text-red-400', medium: 'text-amber-400', low: 'text-emerald-400', neutral: 'text-slate-400' } as const;
const riskBg = { high: 'border-red-500/25 bg-red-500/5', medium: 'border-amber-500/25 bg-amber-500/5', low: 'border-emerald-500/25 bg-emerald-500/5', neutral: 'border-white/5 bg-slate-800/30' } as const;

export default function FeatureGrid({ result }: { result: AnalysisResult }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(result.allFeatures);
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="w-full rounded-xl border border-white/10 py-3 text-sm text-slate-400 transition hover:bg-white/5 hover:text-slate-200"
      >
        {open ? 'Hide' : 'Show'} all 18 extracted features
      </button>
      {open && (
        <div className="animate-rise mt-3 grid grid-cols-1 gap-2 rounded-2xl border border-white/10 bg-white/5 p-4 sm:grid-cols-2">
          {entries.map(([name, data]) => (
            <div key={name} className={`flex items-center justify-between rounded-lg border px-3 py-2 ${riskBg[data.risk as keyof typeof riskBg] ?? riskBg.neutral}`}>
              <span className="text-xs text-slate-300">{name.replaceAll('_', ' ')}</span>
              <span className={`font-mono text-xs ${riskColor[data.risk as keyof typeof riskColor] ?? riskColor.neutral}`}>
                {typeof data.value === 'boolean' ? (data.value ? 'yes' : 'no') : data.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Write SampleUrls.tsx**

```tsx
import { SAMPLE_URLS } from '../lib/classifier';

export default function SampleUrls({ onPick }: { onPick: (url: string) => void }) {
  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <h3 className="font-semibold text-slate-300">Try examples</h3>
      {(['phishing', 'legitimate'] as const).map((kind) => (
        <div key={kind}>
          <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wide">
            <span className={`h-2 w-2 rounded-full ${kind === 'phishing' ? 'bg-red-400' : 'bg-emerald-400'}`} />
            <span className={kind === 'phishing' ? 'text-red-400' : 'text-emerald-400'}>{kind} examples</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_URLS[kind].map((u) => (
              <button
                key={u}
                onClick={() => onPick(u)}
                title={u}
                className={`max-w-xs truncate rounded-lg border px-3 py-1.5 font-mono text-xs transition ${
                  kind === 'phishing'
                    ? 'border-red-500/20 bg-red-500/10 text-red-300 hover:bg-red-500/20'
                    : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20'
                }`}
              >
                {u.length > 44 ? u.slice(0, 44) + '…' : u}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 6: Write HistoryList.tsx**

```tsx
import type { AnalysisResult } from './UrlChecker';

export default function HistoryList({ history, onSelect }: { history: AnalysisResult[]; onSelect: (item: AnalysisResult) => void }) {
  if (history.length === 0) return null;
  return (
    <div className="mx-auto max-w-3xl">
      <h3 className="mb-3 font-semibold text-slate-300">Recent analyses</h3>
      <div className="space-y-2">
        {history.map((item, i) => (
          <button
            key={`${item.url}-${i}`}
            onClick={() => onSelect(item)}
            className={`flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left transition hover:brightness-125 ${
              item.verdict === 'PHISHING' ? 'border-red-500/20 bg-red-950/20' : 'border-emerald-500/20 bg-emerald-950/20'
            }`}
          >
            <span className="max-w-md truncate font-mono text-xs text-slate-400">{item.url}</span>
            <span className={`text-xs font-bold ${item.verdict === 'PHISHING' ? 'text-red-400' : 'text-emerald-400'}`}>
              {item.verdict} · {(item.probability * 100).toFixed(0)}%
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 7: Verify**

```bash
cd phishguard/web && npm run typecheck && npm test && npm run build
```

Expected: all green.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat(web): checker tab with verdict, contributions, samples, history"
```

---

### Task 5: Components — Methodology, Features, Results tabs + App shell

**Files:**
- Create: `phishguard/web/src/components/Methodology.tsx`
- Create: `phishguard/web/src/components/FeatureReference.tsx`
- Create: `phishguard/web/src/components/ResultsPanel.tsx`
- Modify: `phishguard/web/src/App.tsx` (final shell: header, nav, tabs, footer)

**Interfaces:**
- Consumes: `REAL_METRICS`, `RF_IMPORTANCES` from `../lib/modelLoader`; `FEATURE_DESCRIPTIONS` from `../lib/features`.
- Produces: three self-contained section components; App wires tabs.

- [ ] **Step 1: Write Methodology.tsx**

```tsx
const cards = [
  {
    title: 'Problem',
    body: 'Phishing URLs mimic legitimate services to steal credentials. PhishGuard classifies a URL using only its own text — 18 lexical and structural features — with no network calls, DNS, or WHOIS.',
  },
  {
    title: 'Dataset',
    body: '107,355 real URLs: 48,338 verified phishing (PhishTank) + 59,017 legitimate (Tranco top-10k + real benign deep links). Deduplicated, capped at 10 URLs per host so the model learns transferable patterns instead of memorizing hosts.',
  },
  {
    title: 'Model',
    body: 'LogisticRegression (F1 0.80) and RandomForest (F1 0.89) were trained in Python with scikit-learn on an 80/20 stratified split. The LR pipeline is exported to JSON and reproduced exactly in your browser.',
  },
  {
    title: 'Ethics',
    body: 'Missing phishing (false negative) is costlier than a false alarm, so the model is tuned for recall. Verdicts are informational: never rely on one tool for security decisions, and always allow human override.',
  },
];

export default function Methodology() {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h2 className="text-3xl font-bold text-white">Methodology</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {cards.map((c) => (
          <section key={c.title} className="rounded-2xl border border-white/10 bg-white/5 p-6">
            <h3 className="mb-2 font-semibold text-white">{c.title}</h3>
            <p className="text-sm leading-relaxed text-slate-400">{c.body}</p>
          </section>
        ))}
      </div>
      <section className="rounded-2xl border border-amber-500/20 bg-amber-950/20 p-6">
        <h3 className="mb-2 font-semibold text-amber-400">Limitations</h3>
        <p className="text-sm leading-relaxed text-slate-400">
          Lexical features cannot see page content, domain age, or reputation. Clean-looking phishing URLs may pass.
          The model reflects its training data and needs retraining as tactics evolve.
        </p>
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Write FeatureReference.tsx**

```tsx
import { FEATURE_DESCRIPTIONS } from '../lib/features';

export default function FeatureReference() {
  const entries = Object.entries(FEATURE_DESCRIPTIONS);
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white">Feature reference</h2>
        <p className="mt-2 text-slate-400">
          The same 18 features the model was trained on — computed identically in Python and in your browser.
        </p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {entries.map(([name, desc], i) => (
          <div key={name} className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-800 font-mono text-xs text-slate-400">{i + 1}</span>
            <div>
              <div className="font-mono text-sm text-slate-200">{name}</div>
              <div className="mt-0.5 text-xs text-slate-500">{desc}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-amber-500/20 bg-amber-950/20 p-6">
        <h3 className="mb-1 font-semibold text-amber-400">Deliberately excluded: domain age</h3>
        <p className="text-sm text-slate-400">
          WHOIS lookups require network access and break the offline guarantee — excluded by design.
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write ResultsPanel.tsx**

```tsx
import { REAL_METRICS, RF_IMPORTANCES } from '../lib/modelLoader';

const rf = REAL_METRICS.randomForest;
const lr = REAL_METRICS.logisticRegression;
const fmt = (v: number | null) => (v === null ? '—' : v.toFixed(4));
const importances = Object.entries(RF_IMPORTANCES.importances);
const maxImp = importances[0]?.[1] ?? 1;
const cm = rf.confusion;

export default function ResultsPanel() {
  const rows: { metric: string; rf: string; lr: string }[] = [
    { metric: 'Precision', rf: fmt(rf.precision), lr: fmt(lr.precision) },
    { metric: 'Recall', rf: fmt(rf.recall), lr: fmt(lr.recall) },
    { metric: 'F1 score', rf: fmt(rf.f1), lr: fmt(lr.f1) },
    { metric: 'ROC-AUC', rf: fmt(rf.rocAuc), lr: fmt(lr.rocAuc) },
    { metric: '5-fold CV F1', rf: rf.cvF1 ?? '—', lr: lr.cvF1 ?? '—' },
  ];
  const legitPct = ((REAL_METRICS.dataset.legitimate / REAL_METRICS.dataset.totalUrls) * 100).toFixed(1);
  const phishPct = ((REAL_METRICS.dataset.phishing / REAL_METRICS.dataset.totalUrls) * 100).toFixed(1);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white">Model performance</h2>
        <p className="mt-2 text-sm text-slate-400">
          Measured on {REAL_METRICS.dataset.testSetSize.toLocaleString()} held-out URLs. Browser verdicts come from the
          exported LogisticRegression; RandomForest (the stronger model) is shown for comparison.
        </p>
      </div>

      {/* Metrics table */}
      <div className="overflow-x-auto rounded-2xl border border-white/10 bg-white/5 p-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-left text-slate-400">
              <th className="py-2 pr-4 font-medium">Metric</th>
              <th className="py-2 pr-4 text-right font-medium">RandomForest</th>
              <th className="py-2 text-right font-medium">LogisticRegression</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.metric} className="border-b border-white/5 last:border-0">
                <td className="py-2.5 pr-4 text-slate-300">{r.metric}</td>
                <td className="py-2.5 pr-4 text-right font-mono text-slate-200">{r.rf}</td>
                <td className="py-2.5 text-right font-mono text-slate-400">{r.lr}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Confusion matrix */}
      {cm && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="mb-4 font-semibold text-white">Confusion matrix — RandomForest</h3>
          <div className="mx-auto grid w-fit grid-cols-3 gap-1.5 text-center">
            <div />
            <div className="pb-1 text-xs text-slate-500">pred. legit</div>
            <div className="pb-1 text-xs text-slate-500">pred. phish</div>
            <div className="flex items-center pr-2 text-xs text-slate-500">actual legit</div>
            <div className="flex h-24 w-24 flex-col items-center justify-center rounded-xl border border-emerald-500/40 bg-emerald-500/10">
              <span className="text-2xl font-bold text-emerald-400">{cm.tn.toLocaleString()}</span>
              <span className="text-xs text-emerald-300/80">TN</span>
            </div>
            <div className="flex h-24 w-24 flex-col items-center justify-center rounded-xl border border-amber-500/30 bg-amber-500/5">
              <span className="text-2xl font-bold text-amber-400">{cm.fp.toLocaleString()}</span>
              <span className="text-xs text-amber-300/80">FP</span>
            </div>
            <div className="flex items-center pr-2 text-xs text-slate-500">actual phish</div>
            <div className="flex h-24 w-24 flex-col items-center justify-center rounded-xl border border-red-500/30 bg-red-500/5">
              <span className="text-2xl font-bold text-red-400">{cm.fn.toLocaleString()}</span>
              <span className="text-xs text-red-300/80">FN</span>
            </div>
            <div className="flex h-24 w-24 flex-col items-center justify-center rounded-xl border border-emerald-500/40 bg-emerald-500/10">
              <span className="text-2xl font-bold text-emerald-400">{cm.tp.toLocaleString()}</span>
              <span className="text-xs text-emerald-300/80">TP</span>
            </div>
          </div>
        </div>
      )}

      {/* Feature importances */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h3 className="mb-4 font-semibold text-white">Feature importance — RandomForest (top 10)</h3>
        <div className="space-y-2.5">
          {importances.slice(0, 10).map(([name, imp], i) => (
            <div key={name} className="flex items-center gap-3">
              <span className="w-4 text-xs text-slate-500">{i + 1}</span>
              <span className="w-44 truncate font-mono text-xs text-slate-300">{name}</span>
              <div className="h-5 flex-1 overflow-hidden rounded-full bg-slate-800/60">
                <div className="animate-bar h-full rounded-full bg-gradient-to-r from-red-500 to-orange-400" style={{ width: `${(imp / maxImp) * 100}%` }} />
              </div>
              <span className="w-14 text-right font-mono text-xs text-slate-400">{imp.toFixed(3)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Class balance */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h3 className="mb-4 font-semibold text-white">Dataset balance</h3>
        <div className="flex h-8 overflow-hidden rounded-full">
          <div className="flex items-center justify-center bg-gradient-to-r from-emerald-600 to-emerald-500 text-xs font-bold text-white" style={{ width: `${legitPct}%` }}>
            {legitPct}%
          </div>
          <div className="flex items-center justify-center bg-gradient-to-r from-red-500 to-red-600 text-xs font-bold text-white" style={{ width: `${phishPct}%` }}>
            {phishPct}%
          </div>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          {REAL_METRICS.dataset.legitimate.toLocaleString()} legitimate vs {REAL_METRICS.dataset.phishing.toLocaleString()} phishing of {REAL_METRICS.dataset.totalUrls.toLocaleString()} total training URLs.
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Final App.tsx shell**

```tsx
import { useState } from 'react';
import UrlChecker from './components/UrlChecker';
import Methodology from './components/Methodology';
import FeatureReference from './components/FeatureReference';
import ResultsPanel from './components/ResultsPanel';

type TabType = 'checker' | 'methodology' | 'features' | 'results';

const TABS: { id: TabType; label: string }[] = [
  { id: 'checker', label: 'Checker' },
  { id: 'methodology', label: 'Methodology' },
  { id: 'features', label: 'Features' },
  { id: 'results', label: 'Results' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('checker');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-red-500 to-orange-500 text-lg" aria-hidden>
              🛡
            </div>
            <div>
              <h1 className="font-bold leading-tight text-white">PhishGuard</h1>
              <p className="text-xs text-slate-500">ML phishing URL detector · runs in your browser</p>
            </div>
          </div>
          <nav className="flex gap-1" aria-label="Sections">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                aria-current={activeTab === t.id ? 'page' : undefined}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition sm:px-4 ${
                  activeTab === t.id
                    ? 'bg-orange-500/15 text-orange-300'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {activeTab === 'checker' && <UrlChecker />}
        {activeTab === 'methodology' && <Methodology />}
        {activeTab === 'features' && <FeatureReference />}
        {activeTab === 'results' && <ResultsPanel />}
      </main>

      <footer className="mt-16 border-t border-white/10 py-8">
        <div className="mx-auto max-w-7xl space-y-1 px-4 text-center text-xs text-slate-500">
          <p>PhishGuard · LogisticRegression trained on 107,355 real URLs · exported from Python, inference runs fully offline</p>
          <p>Lexical features only — no URL is ever visited. Educational/defensive use; verify before blocking anything.</p>
        </div>
      </footer>
    </div>
  );
}
```

- [ ] **Step 5: Verify**

```bash
cd phishguard/web && npm run typecheck && npm test && npm run build
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(web): methodology, features, results tabs and final app shell"
```

---

### Task 6: README, export-path verification, final checks

**Files:**
- Create: `phishguard/README.md`
- Verify: `phishguard/training/src/export_model.py` targets `../web/src/model/`
- Modify: `phishguard/web/src/lib/modelLoader.ts` docstring (path mention, optional)

- [ ] **Step 1: Write phishguard/README.md (site-first)**

````markdown
# PhishGuard

Machine-learning phishing URL detection — **as a website**. Paste a URL, get an
instant verdict explained feature-by-feature. The trained model runs entirely in
your browser: no server, no network calls, the URL you type never leaves the page.

## Quick start (the site)

```bash
cd web
npm install
npm run dev      # http://localhost:3000
```

Production build: `npm run build` → deploy `web/dist/` to any static host.

## How it works

- 18 lexical/structural features are extracted from the URL string (length,
  entropy, subdomains, TLD-in-subdomain, shorteners, IP hosts, @-symbols, …).
- A **LogisticRegression pipeline trained in Python** on **107,355 real URLs**
  (48,338 verified PhishTank phishing + 59,017 legitimate from Tranco and real
  benign deep links) is exported to JSON (~2 KB) and reproduced exactly in the
  browser: `p = sigmoid(bias + Σ wᵢ·(xᵢ − meanᵢ)/stdᵢ)`.
- Each verdict is explained by **occlusion**: how much does the phishing
  probability change when one feature is swapped to a benign-typical value?
- A RandomForest (test F1 0.888, ROC-AUC 0.954) outperformed LR (F1 0.804) but
  cannot be exported to a browser losslessly — its metrics and feature
  importances are shown on the Results tab.

## Layout

```
phishguard/
├── web/        # the site (React + Vite + TS + Tailwind) — primary deliverable
│   └── src/lib/       # feature extraction + model inference + tests
│   └── src/model/     # exported trained model JSON
└── training/   # Python pipeline: fetch data, train, evaluate, export, CLI
    └── src/check_url.py   # bonus CLI: python src/check_url.py <url>
```

## Retraining (keeps the site in sync)

```bash
cd training
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.fetch_data --custom   # requires raw datasets in data/raw/
python -m src.train                 # trains, evaluates, and re-exports the web model
```

`training/src/export_model.py` writes the refreshed pipeline straight to
`web/src/model/`, so a retrain automatically updates the site.

## Tests

- Web: `cd web && npm test` — feature-parity cases + golden-master tests that
  pin the browser model's outputs to the Python CLI's outputs for 8 URLs.
- Python: `cd training && python src/features_test.py` (std-only) plus the
  CLI regression suite when scikit-learn is installed.

## Ethics & limits

Missing phishing is costlier than a false alarm, so the model favors recall.
It inspects only the URL text — not page content, domain age, or reputation —
and is for educational/defensive use. Never block a URL on this verdict alone.
````

- [ ] **Step 2: Verify export path alignment**

```bash
grep -n 'WEB_SRC =' phishguard/training/src/export_model.py
```

Expected: `WEB_SRC = BASE_DIR.parent / "web" / "src"`.

- [ ] **Step 3: Full verification pass**

```bash
cd phishguard/web && npm run typecheck && npm test && npm run build
python3 phishguard/training/src/features_test.py || true   # stdlib-only suite if python3 available
ls phishing-detector workspace 2>/dev/null && echo 'OLD DIRS STILL PRESENT' || echo 'old dirs gone'
```

Expected: web checks green, old directories absent.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "docs: site-first README and final layout cleanup"
```
