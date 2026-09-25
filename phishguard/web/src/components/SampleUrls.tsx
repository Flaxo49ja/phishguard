import { SAMPLE_URLS } from '../lib/classifier';

export default function SampleUrls({ onPick }: { onPick: (url: string) => void }) {
  return (
    <div className="max-w-3xl space-y-5">
      <h3 className="border-b-2 border-black pb-1 font-mono text-sm font-bold uppercase tracking-wider">Try examples</h3>
      {(['phishing', 'legitimate'] as const).map((kind) => (
        <div key={kind}>
          <div className="mb-2 font-mono text-xs font-bold uppercase tracking-wider">
            <span className={kind === 'phishing' ? 'text-red-700' : 'text-green-700'}>{kind} examples</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_URLS[kind].map((u) => (
              <button
                key={u}
                onClick={() => onPick(u)}
                title={u}
                className={`max-w-xs truncate border-2 px-3 py-1.5 font-mono text-xs transition-colors ${
                  kind === 'phishing'
                    ? 'border-red-700 bg-white text-red-700 hover:bg-red-700 hover:text-white'
                    : 'border-green-700 bg-white text-green-700 hover:bg-green-700 hover:text-white'
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
