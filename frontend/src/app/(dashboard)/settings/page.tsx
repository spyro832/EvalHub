"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { modelsApi, type ModelConfigCreate } from "@/lib/api";

const PROVIDERS = [
  { id: "openai", label: "OpenAI" },
  { id: "anthropic", label: "Anthropic" },
  { id: "google", label: "Google Gemini" },
  { id: "ollama", label: "Ollama (local)" },
  { id: "huggingface", label: "HuggingFace" },
  { id: "other", label: "Other (LiteLLM)" },
];

function AddModelForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ModelConfigCreate>({
    name: "",
    provider: "openai",
    model_id: "",
    api_key: "",
    base_url: "",
    is_local: false,
  });

  const create = useMutation({
    mutationFn: modelsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
      onClose();
    },
  });

  const set = (key: keyof ModelConfigCreate, value: string | boolean) =>
    setForm((f) => ({ ...f, [key]: value }));

  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-800 p-5 space-y-4">
      <h2 className="text-sm font-semibold text-white">Add Model</h2>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Display name</label>
          <input
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            placeholder="e.g. GPT-4o"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Provider</label>
          <select
            value={form.provider}
            onChange={(e) => {
              set("provider", e.target.value);
              set("is_local", e.target.value === "ollama");
            }}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {PROVIDERS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Model ID</label>
          <input
            value={form.model_id}
            onChange={(e) => set("model_id", e.target.value)}
            placeholder="e.g. gpt-4o"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">API Key</label>
          <input
            type="password"
            value={form.api_key ?? ""}
            onChange={(e) => set("api_key", e.target.value)}
            placeholder="sk-…"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        {(form.provider === "ollama" || form.provider === "other") && (
          <div className="sm:col-span-2">
            <label className="block text-xs text-zinc-400 mb-1">Base URL</label>
            <input
              value={form.base_url ?? ""}
              onChange={(e) => set("base_url", e.target.value)}
              placeholder="http://localhost:11434"
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        )}
      </div>

      {create.isError && (
        <p className="text-xs text-red-400">
          Error: {(create.error as Error).message}
        </p>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => create.mutate(form)}
          disabled={!form.name || !form.model_id || create.isPending}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
        >
          {create.isPending ? "Saving…" : "Add Model"}
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

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const { data: models, isLoading } = useQuery({ queryKey: ["models"], queryFn: modelsApi.list });

  const deleteModel = useMutation({
    mutationFn: (id: string) => modelsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["models"] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Settings</h1>
        <p className="mt-1 text-sm text-zinc-400">Manage your AI model configurations.</p>
      </div>

      {/* Models section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Models</h2>
          {!showAdd && (
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Model
            </button>
          )}
        </div>

        {showAdd && <AddModelForm onClose={() => setShowAdd(false)} />}

        <div className="rounded-lg border border-zinc-800 bg-zinc-900">
          {isLoading ? (
            <div className="py-8 text-center text-sm text-zinc-500">Loading…</div>
          ) : !models || models.length === 0 ? (
            <div className="py-8 text-center text-sm text-zinc-500">
              No models configured yet.
            </div>
          ) : (
            <ul className="divide-y divide-zinc-800">
              {models.map((m) => (
                <li key={m.id} className="flex items-center gap-4 px-5 py-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-200">{m.name}</p>
                    <p className="text-xs text-zinc-500">
                      {m.provider} · {m.model_id}
                      {m.is_local && " · local"}
                    </p>
                  </div>
                  <button
                    onClick={() => deleteModel.mutate(m.id)}
                    className="shrink-0 rounded-md p-1.5 text-zinc-600 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
