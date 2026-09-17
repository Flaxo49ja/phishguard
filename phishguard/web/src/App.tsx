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
