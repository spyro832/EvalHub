"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FlaskConical, Plus, Trash2 } from "lucide-react";
import { testSuitesApi, type TestSuiteCreate } from "@/lib/api";

export default function TestSuitesPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
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
      setCasesJson("[]");
    },
  });

  const remove = useMutation({
    mutationFn: testSuitesApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["test-suites"] }),
  });

  const handleCreate = () => {
    try {
      const cases = JSON.parse(casesJson);
      setJsonError(null);
      const payload: TestSuiteCreate = { name, description: description || undefined, category: category || undefined, cases };
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
            Create automated test datasets for regression benchmarking.
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
            <label className="block text-xs text-zinc-400 mb-1">
              Test cases (JSON array)
            </label>
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
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {suites.map((s) => (
            <div key={s.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-zinc-200">{s.name}</p>
                  {s.category && (
                    <span className="mt-1 inline-block rounded-full bg-indigo-900/50 px-2 py-0.5 text-xs text-indigo-300">
                      {s.category}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => remove.mutate(s.id)}
                  className="shrink-0 rounded-md p-1.5 text-zinc-600 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              {s.description && (
                <p className="mt-2 text-xs text-zinc-500 line-clamp-2">{s.description}</p>
              )}
              <p className="mt-3 text-xs text-zinc-600">{s.cases.length} test cases</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
