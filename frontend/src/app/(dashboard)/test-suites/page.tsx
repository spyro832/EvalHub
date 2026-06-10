"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, FlaskConical, Play, Plus, Trash2 } from "lucide-react";
import {
  modelsApi,
  testSuitesApi,
  type RunSSEEvent,
  type TestRun,
  type TestSuite,
  type TestSuiteCreate,
} from "@/lib/api";
import { formatCost, formatLatency } from "@/lib/utils";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { toast } from "@/lib/toast";

// ── Suite card with expandable run panel ─────────────────────────────────────

function SuiteCard({
  suite,
  onDelete,
}: {
  suite: TestSuite;
  onDelete: (suite: TestSuite) => void;
}) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [selectedModel, setSelectedModel] = useState("");
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [liveRun, setLiveRun] = useState<RunSSEEvent | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const { data: models } = useQuery({ queryKey: ["models"], queryFn: modelsApi.list });
  const { data: runs } = useQuery({
    queryKey: ["test-suite-runs", suite.id],
    queryFn: () => testSuitesApi.listRuns(suite.id),
    enabled: expanded,
  });

  // SSE for active run
  useEffect(() => {
    if (!activeRunId) return;

    esRef.current?.close();
    const es = testSuitesApi.streamRun(suite.id, activeRunId);
    esRef.current = es;

    es.onmessage = (event) => {
      const data: RunSSEEvent = JSON.parse(event.data);
      setLiveRun(data);

      if (data.status === "completed" || data.status === "failed") {
        es.close();
        esRef.current = null;
        setActiveRunId(null);
        queryClient.invalidateQueries({ queryKey: ["test-suite-runs", suite.id] });
      }
    };

    es.onerror = () => {
      es.close();
      esRef.current = null;
      setActiveRunId(null);
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [activeRunId, suite.id, queryClient]);

  const runMutation = useMutation({
    mutationFn: () => testSuitesApi.run(suite.id, selectedModel),
    onSuccess: (run: TestRun) => {
      setActiveRunId(run.id);
      setLiveRun({ run_id: run.id, status: "pending", pass_count: 0, fail_count: 0, completed: 0 });
    },
  });

  const isRunning = !!activeRunId;
  const totalCases = suite.cases.length;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900">
      {/* Header */}
      <div className="flex items-start justify-between p-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-zinc-200 truncate">{suite.name}</p>
            {suite.category && (
              <span className="shrink-0 rounded-full bg-indigo-900/50 px-2 py-0.5 text-xs text-indigo-300">
                {suite.category}
              </span>
            )}
          </div>
          {suite.description && (
            <p className="mt-1 text-xs text-zinc-500 line-clamp-1">{suite.description}</p>
          )}
          <p className="mt-1 text-xs text-zinc-600">{totalCases} test cases</p>
        </div>
        <div className="flex items-center gap-1 ml-2 shrink-0">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="rounded-md p-1.5 text-zinc-500 hover:text-zinc-200 transition-colors"
            title={expanded ? "Collapse" : "Expand"}
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          <button
            onClick={() => onDelete(suite)}
            className="rounded-md p-1.5 text-zinc-600 hover:text-red-400 transition-colors"
            title="Delete suite"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Expanded run panel */}
      {expanded && (
        <div className="border-t border-zinc-800 p-4 space-y-4">
          {/* Run controls */}
          <div className="flex items-center gap-2">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="flex-1 rounded-md border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Select a model…</option>
              {models?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
            <button
              disabled={!selectedModel || isRunning}
              onClick={() => runMutation.mutate()}
              className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
            >
              {runMutation.isPending || isRunning ? (
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                <Play className="h-3.5 w-3.5" />
              )}
              {isRunning ? "Running…" : "Run"}
            </button>
          </div>

          {/* Live progress */}
          {isRunning && liveRun && (
            <div className="rounded-md border border-zinc-700 bg-zinc-800 p-3 space-y-2">
              <div className="flex items-center justify-between text-xs text-zinc-400">
                <span className="capitalize font-medium text-blue-400">{liveRun.status}</span>
                <span>{liveRun.completed} / {totalCases} cases</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-700">
                <div
                  className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                  style={{ width: totalCases ? `${(liveRun.completed / totalCases) * 100}%` : "0%" }}
                />
              </div>
              <div className="flex gap-4 text-xs text-zinc-500">
                <span className="text-green-400">✓ {liveRun.pass_count} passed</span>
                <span className="text-red-400">✗ {liveRun.fail_count} failed</span>
              </div>
            </div>
          )}

          {/* Run history */}
          {runs && runs.length > 0 && (
            <div>
              <p className="text-xs font-medium text-zinc-400 mb-2">Run history</p>
              <ul className="space-y-2">
                {runs.map((run) => {
                  const total = run.pass_count + run.fail_count;
                  const passRate = total > 0 ? Math.round((run.pass_count / total) * 100) : 0;
                  const model = models?.find((m) => m.id === run.model_config_id);
                  return (
                    <li
                      key={run.id}
                      className="flex items-center gap-3 rounded-md border border-zinc-700 bg-zinc-800/50 px-3 py-2"
                    >
                      <span
                        className={`h-2 w-2 shrink-0 rounded-full ${
                          run.status === "completed"
                            ? passRate === 100 ? "bg-green-500" : passRate > 50 ? "bg-yellow-500" : "bg-red-500"
                            : run.status === "failed"
                              ? "bg-red-500"
                              : "bg-blue-500 animate-pulse"
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-zinc-300 truncate">
                          {model?.name ?? run.model_config_id}
                        </p>
                        <p className="text-xs text-zinc-600">
                          {new Date(run.created_at).toLocaleString()}
                        </p>
                      </div>
                      {run.status === "completed" && (
                        <div className="shrink-0 flex items-center gap-3 text-xs text-zinc-400">
                          <span className={passRate === 100 ? "text-green-400" : passRate > 50 ? "text-yellow-400" : "text-red-400"}>
                            {passRate}%
                          </span>
                          <span>{run.pass_count}✓ {run.fail_count}✗</span>
                          {run.avg_latency_ms && <span>{formatLatency(run.avg_latency_ms)}</span>}
                          {run.total_cost_usd > 0 && <span>{formatCost(run.total_cost_usd)}</span>}
                        </div>
                      )}
                      {run.status !== "completed" && (
                        <span className="shrink-0 text-xs capitalize text-zinc-500">{run.status}</span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {runs && runs.length === 0 && !isRunning && (
            <p className="text-center text-xs text-zinc-600 py-2">No runs yet. Select a model and click Run.</p>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function TestSuitesPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TestSuite | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [casesJson, setCasesJson] = useState(
    JSON.stringify(
      [{ input: "Write a Python function that reverses a string.", expected_tags: "python,function" }],
      null,
      2
    )
  );
  const [jsonError, setJsonError] = useState<string | null>(null);

  const { data: suites, isLoading } = useQuery({
    queryKey: ["test-suites"],
    queryFn: testSuitesApi.list,
  });

  const create = useMutation({
    mutationFn: testSuitesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["test-suites"] });
      setShowForm(false);
      setName("");
      setDescription("");
      setCategory("");
      setCasesJson("[]");
    },
  });

  const remove = useMutation({
    mutationFn: testSuitesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["test-suites"] });
      toast.success("Test suite deleted");
    },
    onError: (err: Error) => toast.error(`Failed to delete suite: ${err.message}`),
  });

  const handleCreate = () => {
    try {
      const cases = JSON.parse(casesJson);
      setJsonError(null);
      const payload: TestSuiteCreate = {
        name,
        description: description || undefined,
        category: category || undefined,
        cases,
      };
      create.mutate(payload);
    } catch {
      setJsonError("Invalid JSON in test cases");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Test Suites</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Create automated test datasets and run them against any model.
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Suite
        </button>
      </div>

      {showForm && (
        <div className="rounded-lg border border-zinc-700 bg-zinc-800 p-5 space-y-3">
          <h2 className="text-sm font-semibold text-white">New Test Suite</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Suite name"
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <input
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="Category (coding, rag, translation…)"
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <div>
            <label className="block text-xs text-zinc-400 mb-1">Test cases (JSON array)</label>
            <textarea
              value={casesJson}
              onChange={(e) => setCasesJson(e.target.value)}
              rows={8}
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none font-mono"
            />
            {jsonError && <p className="mt-1 text-xs text-red-400">{jsonError}</p>}
            <p className="mt-1 text-xs text-zinc-600">
              Fields per case: input (required), expected_output, expected_tags
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={!name || create.isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              {create.isPending ? "Creating…" : "Create Suite"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="rounded-md border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="py-8 text-center text-sm text-zinc-500">Loading…</div>
      ) : !suites || suites.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <FlaskConical className="h-8 w-8 text-zinc-700" />
          <p className="text-sm text-zinc-500">No test suites yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {suites.map((s) => (
            <SuiteCard key={s.id} suite={s} onDelete={setDeleteTarget} />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Delete test suite?"
        description={`"${deleteTarget?.name}" and all its runs will be permanently deleted.`}
        confirmLabel="Delete"
        onConfirm={() => deleteTarget && remove.mutate(deleteTarget.id)}
      />
    </div>
  );
}
