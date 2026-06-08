"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, BookOpen } from "lucide-react";
import { promptsApi, type PromptCreate } from "@/lib/api";

function PromptCard({
  prompt,
  onDelete,
}: {
  prompt: { id: string; name: string; content: string; tags: string | null; updated_at: string };
  onDelete: (id: string) => void;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-zinc-200">{prompt.name}</p>
          {prompt.tags && (
            <div className="mt-1 flex flex-wrap gap-1">
              {prompt.tags.split(",").map((t) => (
                <span
                  key={t}
                  className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400"
                >
                  {t.trim()}
                </span>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={() => onDelete(prompt.id)}
          className="shrink-0 rounded-md p-1.5 text-zinc-600 hover:text-red-400 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
      <p className="mt-2 text-xs text-zinc-500 line-clamp-2 font-mono">{prompt.content}</p>
    </div>
  );
}

export default function PromptsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<PromptCreate>({ name: "", content: "" });

  const { data: prompts, isLoading } = useQuery({
    queryKey: ["prompts"],
    queryFn: promptsApi.list,
  });

  const create = useMutation({
    mutationFn: promptsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      setForm({ name: "", content: "" });
      setShowForm(false);
    },
  });

  const remove = useMutation({
    mutationFn: promptsApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["prompts"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Prompts</h1>
          <p className="mt-1 text-sm text-zinc-400">Save and reuse prompts across evaluations.</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Prompt
        </button>
      </div>

      {showForm && (
        <div className="rounded-lg border border-zinc-700 bg-zinc-800 p-5 space-y-3">
          <h2 className="text-sm font-semibold text-white">New Prompt</h2>
          <input
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="Prompt name"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <textarea
            value={form.content}
            onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
            rows={5}
            placeholder="Prompt content…"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none font-mono"
          />
          <input
            value={form.tags ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))}
            placeholder="Tags (comma-separated)"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <div className="flex gap-2">
            <button
              onClick={() => create.mutate(form)}
              disabled={!form.name || !form.content || create.isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              {create.isPending ? "Saving…" : "Save"}
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
      ) : !prompts || prompts.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <BookOpen className="h-8 w-8 text-zinc-700" />
          <p className="text-sm text-zinc-500">No prompts saved yet.</p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {prompts.map((p) => (
            <PromptCard key={p.id} prompt={p} onDelete={(id) => remove.mutate(id)} />
          ))}
        </div>
      )}
    </div>
  );
}
