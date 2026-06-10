"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { evaluationsApi, modelsApi, type Evaluation } from "@/lib/api";
import { formatCost, formatLatency } from "@/lib/utils";
import { cn } from "@/lib/utils";

export default function PlaygroundPage() {
  const [promptA, setPromptA] = useState("");
  const [promptB, setPromptB] = useState("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [resultA, setResultA] = useState<Evaluation | null>(null);
  const [resultB, setResultB] = useState<Evaluation | null>(null);

  const { data: models } = useQuery({ queryKey: ["models"], queryFn: modelsApi.list });

  const runA = useMutation({
    mutationFn: evaluationsApi.create,
    onSuccess: (data) => setResultA(data),
  });

  const runB = useMutation({
    mutationFn: evaluationsApi.create,
    onSuccess: (data) => setResultB(data),
  });

  const canRun = selectedModel && (promptA.trim() || promptB.trim());

  const runBoth = () => {
    if (!selectedModel) return;
    if (promptA.trim()) runA.mutate({ prompt: promptA, model_ids: [selectedModel], name: "Playground A" });
    if (promptB.trim()) runB.mutate({ prompt: promptB, model_ids: [selectedModel], name: "Playground B" });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Prompt Playground</h1>
        <p className="mt-1 text-sm text-zinc-400">
          A/B test two prompts on the same model side by side.
        </p>
      </div>

      {/* Model selector */}
      <div className="flex items-center gap-3">
        <label className="text-xs text-zinc-400 shrink-0">Model:</label>
        {!models || models.length === 0 ? (
          <p className="text-xs text-zinc-500">
            <a href="/settings" className="text-indigo-400 hover:underline">Add a model in Settings</a>
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {models.map((m) => (
              <button
                key={m.id}
                onClick={() => setSelectedModel(m.id)}
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-medium transition-colors",
                  selectedModel === m.id
                    ? "bg-indigo-600 text-white"
                    : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                )}
              >
                {m.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Split prompts */}
      <div className="grid gap-4 lg:grid-cols-2">
        {(["A", "B"] as const).map((side) => {
          const value = side === "A" ? promptA : promptB;
          const setValue = side === "A" ? setPromptA : setPromptB;
          const result = side === "A" ? resultA : resultB;
          const running = side === "A" ? runA.isPending : runB.isPending;

          return (
            <div key={side} className="space-y-3">
              <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs font-bold text-zinc-300">
                    Prompt {side}
                  </span>
                </div>
                <textarea
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  rows={6}
                  placeholder={`Enter prompt ${side}…`}
                  className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
                />
              </div>

              {/* Result */}
              {result && result.results[0] && (
                <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs font-medium text-indigo-400">Result {side}</span>
                    <div className="flex gap-2 text-xs text-zinc-500">
                      {result.results[0].latency_ms && (
                        <span>{formatLatency(result.results[0].latency_ms)}</span>
                      )}
                      {result.results[0].cost_usd !== null && (
                        <span>{formatCost(result.results[0].cost_usd ?? 0)}</span>
                      )}
                    </div>
                    {running && (
                      <span className="ml-auto h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-500/30 border-t-indigo-500" />
                    )}
                  </div>
                  {result.results[0].error ? (
                    <p className="text-xs text-red-400">{result.results[0].error}</p>
                  ) : (
                    <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
                      {result.results[0].response}
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <button
        disabled={!canRun || runA.isPending || runB.isPending}
        onClick={runBoth}
        className="flex items-center gap-2 rounded-md bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
      >
        {runA.isPending || runB.isPending ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Running…
          </>
        ) : (
          <>
            <Play className="h-4 w-4" />
            Run Both
          </>
        )}
      </button>
    </div>
  );
}
