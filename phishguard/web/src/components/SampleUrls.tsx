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
