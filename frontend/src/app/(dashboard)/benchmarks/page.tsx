"use client";

import { Beaker } from "lucide-react";

export default function BenchmarksPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Community Benchmarks</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Browse, import, and share benchmark datasets with the community.
        </p>
      </div>

      <div className="flex flex-col items-center gap-3 py-20 text-center">
        <Beaker className="h-10 w-10 text-zinc-700" />
        <p className="text-sm font-medium text-zinc-400">Coming soon — Phase 4</p>
        <p className="text-xs text-zinc-600 max-w-sm">
          The Community Benchmark Registry will let you share and discover benchmark datasets for
          coding, RAG, translation, customer support, and more.
        </p>
      </div>
    </div>
  );
}
