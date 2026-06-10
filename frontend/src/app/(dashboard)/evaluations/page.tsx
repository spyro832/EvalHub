"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Play } from "lucide-react";
import { evaluationsApi, modelsApi, type EvalSSEEvent, type Evaluation } from "@/lib/api";
import { formatCost, formatLatency, truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";

const COLORS = [
  "#6366f1", "#22c55e", "#f59e0b", "#ef4444",
  "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16",
];

export default function EvaluationsPage() {
  const queryClient = useQueryClient();
  const [prompt, setPrompt] = useState("");
  const [evalName, setEvalName] = useState("");
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [activeEval, setActiveEval] = useState<Evaluation | null>(null);
  const [progress, setProgress] = useState<{ completed: number; total: number } | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const { data: models } = useQuery({ queryKey: ["models"], queryFn: modelsApi.list });
  const { data: evaluations } = useQuery({
    queryKey: ["evaluations"],
    queryFn: evaluationsApi.list,
    refetchInterval: activeEval && ["pending", "running"].includes(activeEval.status) ? 3000 : false,
  });

  // Open SSE stream once we have a pending/running evaluation
  useEffect(() => {
    if (!activeEval || !["pending", "running"].includes(activeEval.status)) return;

    // Close any existing stream
    esRef.current?.close();

    const es = evaluationsApi.stream(activeEval.id);
    esRef.current = es;

    es.onmessage = (event) => {
      const data: EvalSSEEvent = JSON.parse(event.data);

      if (data.error) {
        es.close();
        return;
      }

      setProgress({ completed: data.completed, total: data.total });

      if (data.status === "completed" || data.status === "failed") {
        es.close();
        esRef.current = null;
        setProgress(null);
        // Fetch the full evaluation with results
        evaluationsApi.get(activeEval.id).then(setActiveEval).catch(console.error);
        queryClient.invalidateQueries({ queryKey: ["evaluations"] });
      }
    };

    es.onerror = () => {
      es.close();
      esRef.current = null;
      setProgress(null);
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [activeEval?.id, activeEval?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const runEval = useMutation({
    mutationFn: evaluationsApi.create,
    onSuccess: (data) => {
      setActiveEval(data);
      setProgress({ completed: 0, total: selectedModels.length });
      queryClient.invalidateQueries({ queryKey: ["evaluations"] });
    },
  });

  const toggleModel = (id: string) => {
    setSelectedModels((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    );
  };

  const canRun = prompt.trim().length > 0 && selectedModels.length > 0;
  const isStreaming = activeEval && ["pending", "running"].includes(activeEval.status);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Model Comparison</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Run the same prompt across multiple models and compare results.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input panel */}
        <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900 p-5">
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1">
              Evaluation name (optional)
            </label>
            <input
              value={evalName}
              onChange={(e) => setEvalName(e.target.value)}
              placeholder="e.g. Coding benchmark v1"
              className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1">Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={6}
              placeholder="Enter your prompt here…"
              className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-2">
              Select models ({selectedModels.length} selected)
            </label>
            {!models || models.length === 0 ? (
              <p className="text-xs text-zinc-500">
                No models configured.{" "}
                <a href="/settings" className="text-indigo-400 hover:underline">
                  Add one in Settings.
                </a>
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {models.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => toggleModel(m.id)}
                    className={cn(
                      "rounded-full px-3 py-1 text-xs font-medium transition-colors",
                      selectedModels.includes(m.id)
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

          <button
            disabled={!canRun || runEval.isPending || !!isStreaming}
            onClick={() =>
              runEval.mutate({
                prompt,
                model_ids: selectedModels,
                name: evalName || undefined,
              })
            }
            className="flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
          >
            {runEval.isPending ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Queuing…
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Run Evaluation
              </>
            )}
          </button>
        </div>

        {/* Results panel */}
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-white">
              {activeEval ? "Results" : "Results will appear here"}
            </h2>
            {isStreaming && progress && (
              <span className="text-xs text-zinc-400">
                {progress.completed}/{progress.total} models
              </span>
            )}
          </div>

          {/* Progress bar while streaming */}
          {isStreaming && progress && (
            <div className="mb-4 space-y-2">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
                <div
                  className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                  style={{ width: progress.total ? `${(progress.completed / progress.total) * 100}%` : "0%" }}
                />
              </div>
              <p className="text-xs text-zinc-500 text-center">
                Running models — {progress.completed} of {progress.total} complete…
              </p>
            </div>
          )}

          {activeEval && activeEval.results.length > 0 && !isStreaming && (
            <div className="space-y-4">
              {/* Latency chart */}
              <div>
                <p className="text-xs text-zinc-400 mb-2">Latency (ms)</p>
                <ResponsiveContainer width="100%" height={120}>
                  <BarChart data={activeEval.results.filter((r) => r.latency_ms)}>
                    <XAxis dataKey="model_config_id" tick={false} />
                    <YAxis tick={{ fontSize: 10, fill: "#71717a" }} />
                    <Tooltip
                      formatter={(v) => [formatLatency(Number(v)), "Latency"]}
                      contentStyle={{
                        background: "#18181b",
                        border: "1px solid #3f3f46",
                        borderRadius: "6px",
                        fontSize: "12px",
                      }}
                    />
                    <Bar dataKey="latency_ms" radius={[3, 3, 0, 0]}>
                      {activeEval.results.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Result cards */}
              <div className="space-y-3">
                {activeEval.results.map((result, i) => {
                  const model = models?.find((m) => m.id === result.model_config_id);
                  return (
                    <div key={result.id} className="rounded-md border border-zinc-700 p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span
                          className="text-xs font-medium"
                          style={{ color: COLORS[i % COLORS.length] }}
                        >
                          {model?.name ?? result.model_config_id}
                        </span>
                        <div className="flex gap-3 text-xs text-zinc-500">
                          {result.latency_ms && <span>{formatLatency(result.latency_ms)}</span>}
                          {result.cost_usd !== null && (
                            <span>{formatCost(result.cost_usd ?? 0)}</span>
                          )}
                          {result.input_tokens && (
                            <span>{result.input_tokens + (result.output_tokens ?? 0)} tokens</span>
                          )}
                        </div>
                      </div>
                      {result.error ? (
                        <p className="text-xs text-red-400">{result.error}</p>
                      ) : (
                        <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
                          {result.response ?? "No response"}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* History */}
      {evaluations && evaluations.length > 0 && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900">
          <div className="border-b border-zinc-800 px-5 py-3">
            <h2 className="text-sm font-medium text-white">History</h2>
          </div>
          <ul className="divide-y divide-zinc-800">
            {evaluations.map((ev) => (
              <li
                key={ev.id}
                className="flex items-center gap-4 px-5 py-3 hover:bg-zinc-800/50 cursor-pointer transition-colors"
                onClick={() =>
                  evaluationsApi.get(ev.id).then(setActiveEval).catch(console.error)
                }
              >
                <span
                  className={`h-2 w-2 shrink-0 rounded-full ${
                    ev.status === "completed"
                      ? "bg-green-500"
                      : ev.status === "failed"
                        ? "bg-red-500"
                        : ev.status === "running"
                          ? "bg-blue-500 animate-pulse"
                          : "bg-yellow-500 animate-pulse"
                  }`}
                />
                <span className="flex-1 truncate text-sm text-zinc-300">
                  {ev.name ?? truncate(ev.prompt, 80)}
                </span>
                <span
                  className={`shrink-0 text-xs font-medium ${
                    ev.status === "completed" ? "text-green-500" :
                    ev.status === "failed" ? "text-red-500" :
                    "text-yellow-500"
                  }`}
                >
                  {ev.status}
                </span>
                <span className="shrink-0 text-xs text-zinc-500">
                  {new Date(ev.created_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
