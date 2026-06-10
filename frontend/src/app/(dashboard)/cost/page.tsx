"use client";

import { useQuery } from "@tanstack/react-query";
import { costApi } from "@/lib/api";
import { formatCost, formatTokens } from "@/lib/utils";
// recharts imports ready for future per-model chart (Step 10)
// import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function CostPage() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ["cost-summary"],
    queryFn: costApi.summary,
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-zinc-500 text-sm">
        Loading…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Cost Analytics</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Track your AI spending across all models and providers.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
          <p className="text-xs text-zinc-400">Total Spent</p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {summary ? formatCost(summary.total_usd) : "—"}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
          <p className="text-xs text-zinc-400">API Calls</p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary?.total_calls ?? 0}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
          <p className="text-xs text-zinc-400">Input Tokens</p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {summary ? formatTokens(summary.total_input_tokens) : "—"}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
          <p className="text-xs text-zinc-400">Output Tokens</p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {summary ? formatTokens(summary.total_output_tokens) : "—"}
          </p>
        </div>
      </div>

      {/* Cost per call */}
      {summary && summary.total_calls > 0 && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
          <h2 className="text-sm font-medium text-white mb-1">Average Cost Per Call</h2>
          <p className="text-3xl font-semibold text-indigo-400">
            {formatCost(summary.total_usd / summary.total_calls)}
          </p>
        </div>
      )}

      {(!summary || summary.total_calls === 0) && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 py-16 text-center">
          <p className="text-sm text-zinc-500">
            No cost data yet. Run some evaluations to see spending analytics.
          </p>
        </div>
      )}
    </div>
  );
}
