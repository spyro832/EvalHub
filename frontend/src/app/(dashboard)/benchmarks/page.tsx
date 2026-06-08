"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Beaker, Download, Play, Plus, Trash2, Upload, ChevronDown, ChevronUp } from "lucide-react";
import {
  benchmarksApi,
  modelsApi,
  type Benchmark,
  type BenchmarkRunResult,
} from "@/lib/api";

const CATEGORY_COLORS: Record<string, string> = {
  coding: "bg-blue-900/40 text-blue-300",
  rag: "bg-purple-900/40 text-purple-300",
  translation: "bg-green-900/40 text-green-300",
  other: "bg-zinc-800 text-zinc-400",
};

function CategoryBadge({ category }: { category: string | null }) {
  const cls = CATEGORY_COLORS[category ?? "other"] ?? CATEGORY_COLORS.other;
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {category ?? "general"}
    </span>
  );
}

function RunResultPanel({ result }: { result: BenchmarkRunResult }) {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.round(result.pass_rate * 100);

  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-800/60 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-white">Run Results</span>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1"
        >
          {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {expanded ? "Hide" : "Show"} details
        </button>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Pass rate", value: `${pct}%`, color: pct >= 70 ? "text-green-400" : pct >= 40 ? "text-yellow-400" : "text-red-400" },
          { label: "Passed", value: result.pass_count, color: "text-green-400" },
          { label: "Failed", value: result.fail_count, color: "text-red-400" },
          { label: "Avg latency", value: result.avg_latency_ms ? `${Math.round(result.avg_latency_ms)}ms` : "—", color: "text-zinc-300" },
        ].map((s) => (
          <div key={s.label} className="rounded-md bg-zinc-900 p-2 text-center">
            <p className={`text-lg font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-zinc-500">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Pass rate bar */}
      <div className="h-2 w-full rounded-full bg-zinc-700">
        <div
          className={`h-2 rounded-full transition-all ${pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {expanded && (
        <div className="space-y-1 max-h-64 overflow-y-auto">
          {result.results.map((r, i) => (
            <div key={r.item_id} className="rounded border border-zinc-700 bg-zinc-900 p-2 text-xs">
              <div className="flex items-start gap-2">
                <span className={`shrink-0 font-bold ${r.passed ? "text-green-400" : "text-red-400"}`}>
                  {r.passed ? "✓" : "✗"}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-zinc-400 truncate">{r.input}</p>
                  <p className="text-zinc-200 mt-0.5 line-clamp-2">{r.response}</p>
                </div>
                {r.latency_ms != null && (
                  <span className="shrink-0 text-zinc-600">{Math.round(r.latency_ms)}ms</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BenchmarkCard({ benchmark }: { benchmark: Benchmark }) {
  const queryClient = useQueryClient();
  const { data: models } = useQuery({ queryKey: ["models"], queryFn: modelsApi.list });
  const [selectedModel, setSelectedModel] = useState("");
  const [itemLimit, setItemLimit] = useState<number | undefined>(undefined);
  const [runResult, setRunResult] = useState<BenchmarkRunResult | null>(null);
  const [showItems, setShowItems] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => benchmarksApi.delete(benchmark.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["benchmarks"] }),
  });

  const runMutation = useMutation({
    mutationFn: () => benchmarksApi.run(benchmark.id, selectedModel, itemLimit),
    onSuccess: (data) => setRunResult(data),
  });

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-white">{benchmark.name}</h3>
            <CategoryBadge category={benchmark.category} />
          </div>
          {benchmark.description && (
            <p className="mt-1 text-xs text-zinc-400 line-clamp-2">{benchmark.description}</p>
          )}
          <p className="mt-1 text-xs text-zinc-600">
            {benchmark.item_count} items
            {benchmark.author && ` · by ${benchmark.author}`}
          </p>
        </div>
        <div className="flex shrink-0 gap-1">
          <a
            href={benchmarksApi.exportUrl(benchmark.id)}
            download
            className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
            title="Export JSON"
          >
            <Download className="h-4 w-4" />
          </a>
          <button
            onClick={() => deleteMutation.mutate()}
            className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-red-400 transition-colors"
            aria-label="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Preview items */}
      {benchmark.items.length > 0 && (
        <div>
          <button
            onClick={() => setShowItems(!showItems)}
            className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1"
          >
            {showItems ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {showItems ? "Hide" : "Preview"} items
          </button>
          {showItems && (
            <ul className="mt-2 space-y-1 max-h-40 overflow-y-auto">
              {benchmark.items.slice(0, 10).map((item) => (
                <li key={item.id} className="rounded bg-zinc-800 px-2 py-1 text-xs text-zinc-300 truncate">
                  {item.input}
                </li>
              ))}
              {benchmark.items.length > 10 && (
                <li className="text-xs text-zinc-600 px-2">…and {benchmark.items.length - 10} more</li>
              )}
            </ul>
          )}
        </div>
      )}

      {/* Run controls */}
      <div className="flex gap-2 flex-wrap items-end">
        <div className="flex-1 min-w-36">
          <label className="block text-xs text-zinc-500 mb-1">Model</label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full rounded border border-zinc-700 bg-zinc-800 px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">— select model —</option>
            {models?.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </div>
        <div className="w-24">
          <label className="block text-xs text-zinc-500 mb-1">Limit</label>
          <input
            type="number"
            min={1}
            max={500}
            placeholder="all"
            value={itemLimit ?? ""}
            onChange={(e) => setItemLimit(e.target.value ? Number(e.target.value) : undefined)}
            className="w-full rounded border border-zinc-700 bg-zinc-800 px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <button
          onClick={() => runMutation.mutate()}
          disabled={!selectedModel || runMutation.isPending}
          className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
        >
          <Play className="h-3 w-3" />
          {runMutation.isPending ? "Running…" : "Run"}
        </button>
      </div>

      {runMutation.isError && (
        <p className="text-xs text-red-400">
          Error: {(runMutation.error as Error).message}
        </p>
      )}

      {runResult && <RunResultPanel result={runResult} />}
    </div>
  );
}

function ImportForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [json, setJson] = useState("");
  const [error, setError] = useState("");

  const importMutation = useMutation({
    mutationFn: (data: Parameters<typeof benchmarksApi.import>[0]) => benchmarksApi.import(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["benchmarks"] });
      onClose();
    },
    onError: (e) => setError((e as Error).message),
  });

  const handleImport = () => {
    setError("");
    try {
      const parsed = JSON.parse(json);
      importMutation.mutate(parsed);
    } catch {
      setError("Invalid JSON — please check the format.");
    }
  };

  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-800 p-5 space-y-3">
      <h2 className="text-sm font-semibold text-white">Import Benchmark (JSON)</h2>
      <p className="text-xs text-zinc-400">
        Paste a benchmark JSON object with <code className="text-indigo-300">name</code> and{" "}
        <code className="text-indigo-300">items</code> fields.
      </p>
      <textarea
        rows={8}
        value={json}
        onChange={(e) => setJson(e.target.value)}
        placeholder={`{\n  "name": "My Benchmark",\n  "category": "coding",\n  "items": [\n    { "input": "...", "expected_tags": "def,return" }\n  ]\n}`}
        className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={handleImport}
          disabled={!json.trim() || importMutation.isPending}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
        >
          {importMutation.isPending ? "Importing…" : "Import"}
        </button>
        <button
          onClick={onClose}
          className="rounded-md border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export default function BenchmarksPage() {
  const [showImport, setShowImport] = useState(false);
  const { data: benchmarks, isLoading } = useQuery({
    queryKey: ["benchmarks"],
    queryFn: benchmarksApi.list,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Community Benchmarks</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Browse, run, import, and share benchmark datasets.
          </p>
        </div>
        {!showImport && (
          <button
            onClick={() => setShowImport(true)}
            className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            <Upload className="h-3.5 w-3.5" />
            Import JSON
          </button>
        )}
      </div>

      {showImport && <ImportForm onClose={() => setShowImport(false)} />}

      {isLoading ? (
        <div className="py-16 text-center text-sm text-zinc-500">Loading…</div>
      ) : !benchmarks || benchmarks.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20 text-center">
          <Beaker className="h-10 w-10 text-zinc-700" />
          <p className="text-sm font-medium text-zinc-400">No benchmarks yet</p>
          <p className="text-xs text-zinc-600 max-w-sm">
            Import a JSON benchmark or run <code className="text-indigo-400">make seed</code> to
            load the sample coding, RAG, and translation benchmarks.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
          {benchmarks.map((b) => (
            <BenchmarkCard key={b.id} benchmark={b} />
          ))}
        </div>
      )}
    </div>
  );
}

