import React from 'react';
import { Sparkles, AlertCircle, TrendingUp, Volume2, Calendar } from 'lucide-react';

interface WhatChangedFeedProps {
  feed: string[];
}

export const WhatChangedFeed: React.FC<WhatChangedFeedProps> = ({ feed }) => {
  if (!feed || feed.length === 0) return null;

  const getIconForText = (text: string) => {
    const lower = text.toLowerCase();
    if (lower.includes('volume')) return Volume2;
    if (lower.includes('earnings') || lower.includes('event')) return Calendar;
    if (lower.includes('strengthened') || lower.includes('momentum') || lower.includes('trend')) return TrendingUp;
    return AlertCircle;
  };

  return (
    <div className="space-y-3 my-6">
      <div className="flex items-center space-x-2">
        <Sparkles className="w-4 h-4 text-blue-500" />
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          What Changed? (Delta Intelligence)
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {feed.map((item, idx) => {
          const Icon = getIconForText(item);
          return (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark flex items-start space-x-3 shadow-subtle hover:border-blue-500/40 transition-colors"
            >
              <div className="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5">
                <Icon className="w-4 h-4" />
              </div>
              <p className="text-xs text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
                {item}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
