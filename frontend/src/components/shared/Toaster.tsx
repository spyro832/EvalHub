"use client";

import { CheckCircle2, Info, X, XCircle } from "lucide-react";
import { useToastStore, type Toast } from "@/lib/toast";

const icons = {
  success: <CheckCircle2 className="h-4 w-4 text-green-400 shrink-0" />,
  error: <XCircle className="h-4 w-4 text-red-400 shrink-0" />,
  info: <Info className="h-4 w-4 text-blue-400 shrink-0" />,
};

const borders = {
  success: "border-green-800/60",
  error: "border-red-800/60",
  info: "border-blue-800/60",
};

function ToastItem({ toast }: { toast: Toast }) {
  const remove = useToastStore((s) => s.remove);

  return (
    <div
      className={`flex items-start gap-3 rounded-lg border bg-zinc-900 px-4 py-3 shadow-lg min-w-[280px] max-w-sm ${borders[toast.type]}`}
    >
      {icons[toast.type]}
      <p className="flex-1 text-sm text-zinc-200 leading-snug">{toast.message}</p>
      <button
        onClick={() => remove(toast.id)}
        className="shrink-0 rounded p-0.5 text-zinc-500 hover:text-zinc-200 transition-colors"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}
