import { useState } from 'react';
import UrlChecker from './components/UrlChecker';

type TabType = 'checker' | 'methodology' | 'features' | 'results';

export default function App() {
  const [activeTab] = useState<TabType>('checker');
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto max-w-7xl px-4 py-8">
        {activeTab === 'checker' && <UrlChecker />}
      </main>
    </div>
  );
}
