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
    <div className="min-h-screen bg-white text-neutral-950">
      <header className="sticky top-0 z-40 border-b-2 border-black bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="font-mono text-lg font-bold uppercase tracking-tight text-black">PhishGuard</span>
            <span className="hidden border-l-2 border-black pl-3 text-xs text-neutral-600 sm:inline">
              ML phishing URL detector · offline
            </span>
          </div>
          <nav className="flex gap-0" aria-label="Sections">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                aria-current={activeTab === t.id ? 'page' : undefined}
                className={`border-2 border-black px-3 py-1.5 font-mono text-sm font-bold uppercase tracking-wide transition-colors sm:px-4 ${
                  activeTab === t.id
                    ? 'bg-black text-white'
                    : '-ml-[2px] bg-white text-black hover:bg-neutral-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10">
        {activeTab === 'checker' && <UrlChecker />}
        {activeTab === 'methodology' && <Methodology />}
        {activeTab === 'features' && <FeatureReference />}
        {activeTab === 'results' && <ResultsPanel />}
      </main>

      <footer className="mt-16 border-t-2 border-black py-6">
        <div className="mx-auto max-w-6xl space-y-1 px-4 font-mono text-xs text-neutral-600">
          <p>PhishGuard — LogisticRegression trained on 107,355 real URLs. Exported from Python; inference runs fully offline.</p>
          <p>Lexical features only. No URL is ever visited. Educational/defensive use — verify before blocking anything.</p>
        </div>
      </footer>
    </div>
  );
}
