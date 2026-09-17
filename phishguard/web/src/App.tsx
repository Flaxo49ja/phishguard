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
