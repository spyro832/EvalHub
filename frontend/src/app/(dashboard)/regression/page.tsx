"use client";

import { TrendingDown } from "lucide-react";

export default function RegressionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Regression Detection</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Track quality changes across model versions and prompt updates.
        </p>
      </div>

      <div className="flex flex-col items-center gap-3 py-20 text-center">
        <TrendingDown className="h-10 w-10 text-zinc-700" />
        <p className="text-sm font-medium text-zinc-400">Coming in the next session</p>
        <p className="text-xs text-zinc-600 max-w-sm">
          Run the same test suite multiple times across different models or over time. EvalHub will
          highlight score degradations automatically.
        </p>
      </div>
    </div>
  );
}
