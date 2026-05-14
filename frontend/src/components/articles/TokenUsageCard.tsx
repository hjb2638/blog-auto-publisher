import { useState } from 'react';

interface TokenBreakdown {
  input: number;
  output: number;
}

interface TokenUsageCardProps {
  tokenUsage: Record<string, TokenBreakdown>;
}

const STAGE_LABELS: Record<string, string> = {
  outline: 'Outline',
  images: 'Image Plan',
};

function stageLabel(key: string): string {
  if (STAGE_LABELS[key]) return STAGE_LABELS[key];
  const m = key.match(/^content_(\d+)$/);
  if (m) return `Section ${m[1]}`;
  return key;
}

export default function TokenUsageCard({ tokenUsage }: TokenUsageCardProps) {
  const [expanded, setExpanded] = useState(false);

  const stages = Object.entries(tokenUsage);
  if (stages.length === 0) return null;

  const grandTotal = stages.reduce(
    (sum, [, v]) => sum + (v.input || 0) + (v.output || 0),
    0,
  );

  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-2xl transition-colors"
      >
        <span>Token Usage &mdash; {grandTotal.toLocaleString()} total</span>
        <span className="text-gray-400 text-xs">
          {expanded ? '▲' : '▼'}
        </span>
      </button>
      {expanded && (
        <div className="border-t border-gray-100 p-4 space-y-2">
          {stages.map(([key, val]) => {
            const stageTotal = (val.input || 0) + (val.output || 0);
            return (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-gray-500 w-28">{stageLabel(key)}</span>
                <span className="text-gray-400 font-mono w-16 text-right">
                  {val.input?.toLocaleString() ?? 0}
                </span>
                <span className="text-gray-400 mx-1">+</span>
                <span className="text-gray-400 font-mono w-16 text-right">
                  {val.output?.toLocaleString() ?? 0}
                </span>
                <span className="text-gray-400 mx-1">=</span>
                <span className="text-gray-700 font-mono w-16 text-right font-medium">
                  {stageTotal.toLocaleString()}
                </span>
              </div>
            );
          })}
          <div className="flex items-center justify-between text-xs font-semibold pt-2 border-t border-gray-100">
            <span className="text-gray-700 w-28">Total</span>
            <span className="text-gray-400 font-mono w-16 text-right">
              {stages.reduce((s, [, v]) => s + (v.input || 0), 0).toLocaleString()}
            </span>
            <span className="text-gray-400 mx-1">+</span>
            <span className="text-gray-400 font-mono w-16 text-right">
              {stages.reduce((s, [, v]) => s + (v.output || 0), 0).toLocaleString()}
            </span>
            <span className="text-gray-400 mx-1">=</span>
            <span className="text-gray-900 font-mono w-16 text-right">
              {grandTotal.toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
