"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Minus,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { regressionApi, type SuiteSummary } from "@/lib/api";

// ── Colour palette for model lines ────────────────────────────────────────

const MODEL_COLORS = [
  "#6366f1", // indigo
  "#10b981", // emerald
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // violet
  "#06b6d4", // cyan
  "#f97316", // orange
  "#ec4899", // pink
];

// ── Helpers ───────────────────────────────────────────────────────────────

function DeltaBadge({ delta }: { delta: number }) {
  const pct = Math.round(delta * 100);
  if (pct < -2) {
    return (
      <span className="flex items-center gap-0.5 text-red-400 text-xs font-medium">
        <TrendingDown className="h-3 w-3" />
        {pct}%
      </span>
    );
  }
  if (pct > 2) {
    return (
      <span className="flex items-center gap-0.5 text-green-400 text-xs font-medium">
        <TrendingUp className="h-3 w-3" />+{pct}%
      </span>
    );
  }
  return (
    <span className="flex items-center gap-0.5 text-zinc-500 text-xs">
      <Minus className="h-3 w-3" /> stable
    </span>
  );
}

/** Tiny inline SVG sparkline for the suite card. */
function MiniSparkline({ data }: { data: number[] }) {
  if (data.length < 2) return null;
  const W = 80;
  const H = 28;
  const max = Math.max(...data, 0.01);
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * W;
      const y = H - (v / max) * (H - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const isDown = data[data.length - 1] < data[0] - 0.05;
  const color = isDown ? "#ef4444" : "#6366f1";

  return (
    <svg width={W} height={H} className="shrink-0" aria-hidden>
      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

// ── Trend chart (lazy-loaded when user expands a card) ────────────────────

function TrendChart({ suiteId }: { suiteId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["regression-trend", suiteId],
    queryFn: () => regressionApi.getTrend(suiteId),
  });

  if (isLoading) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-zinc-500">
        Loading chart…
      </div>
    );
  }
  if (!data || data.runs.length === 0) {
    return (
      <div className="h-24 flex items-center justify-center text-xs text-zinc-500">
        No completed runs to chart yet.
      </div>
    );
  }

  // Collect unique model names (order of first appearance)
  const modelNames = [...new Set(data.runs.map((r) => r.model_name))];

  // Build a unified timeline: one entry per unique millisecond timestamp
  // Each entry has { label, [modelName]: passRatePct }
  const timeMap = new Map<number, Record<string, string | number>>();
  const sorted = [...data.runs].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  sorted.forEach((run) => {
    const t = new Date(run.created_at).getTime();
    if (!timeMap.has(t)) {
      const label = new Date(run.created_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
      timeMap.set(t, { label });
    }
    timeMap.get(t)![run.model_name] = Math.round(run.pass_rate * 100);
  });

  const chartData = [...timeMap.values()];

  return (
    <div className="mt-4 rounded-lg border border-zinc-700 bg-zinc-800/40 p-4">
      <p className="text-xs font-medium text-zinc-400 mb-3">Pass rate over time (%)</p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
          <XAxis
            dataKey="label"
            tick={{ fill: "#a1a1aa", fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "#a1a1aa", fontSize: 10 }}
            tickFormatter={(v) => `${v}%`}
            width={36}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "1px solid #3f3f46",
              borderRadius: 6,
              fontSize: 12,
            }}
            labelStyle={{ color: "#a1a1aa", marginBottom: 4 }}
            formatter={(value) => [`${value}%`]}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: "#a1a1aa", paddingTop: 8 }} />
          {modelNames.map((name, i) => (
            <Line
              key={name}
              type="monotone"
              dataKey={name}
              stroke={MODEL_COLORS[i % MODEL_COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3, fill: MODEL_COLORS[i % MODEL_COLORS.length] }}
              activeDot={{ r: 5 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Suite card ────────────────────────────────────────────────────────────

function SuiteCard({ suite }: { suite: SuiteSummary }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`rounded-lg border bg-zinc-900 p-5 space-y-4 transition-colors ${
        suite.has_regression ? "border-red-800/60" : "border-zinc-800"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          {suite.has_regression && (
            <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
          )}
          <h3 className="text-sm font-semibold text-white">{suite.suite_name}</h3>
          {suite.category && (
            <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">
              {suite.category}
            </span>
          )}
          {suite.has_regression && (
            <span className="rounded-full bg-red-900/40 px-2 py-0.5 text-xs text-red-400 font-medium">
              Regression detected
            </span>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="shrink-0 flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {expanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
          {expanded ? "Hide" : "View"} trend
        </button>
      </div>

      {/* Per-model rows */}
      <div className="space-y-3">
        {suite.models.map((model) => {
          const pct = Math.round(model.latest_pass_rate * 100);
          return (
            <div key={model.model_config_id} className="flex items-center gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-xs font-medium text-zinc-200 truncate">
                    {model.model_name}
                  </span>
                  {model.has_regression && (
                    <AlertTriangle className="h-3 w-3 text-red-400 shrink-0" />
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span
                    className={`text-xs font-semibold ${
                      pct >= 70
                        ? "text-green-400"
                        : pct >= 40
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {pct}%
                  </span>
                  <DeltaBadge delta={model.delta} />
                  <span className="text-xs text-zinc-600">
                    {model.run_count} run{model.run_count !== 1 ? "s" : ""}
                  </span>
                </div>
              </div>

              {/* Mini sparkline */}
              <MiniSparkline data={model.sparkline} />
            </div>
          );
        })}
      </div>

      {/* Expanded trend chart */}
      {expanded && <TrendChart suiteId={suite.suite_id} />}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function RegressionPage() {
  const { data: suites, isLoading } = useQuery({
    queryKey: ["regression-suites"],
    queryFn: regressionApi.getSuitesSummary,
  });

  const regressionCount = suites?.filter((s) => s.has_regression).length ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-white">Regression Detection</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Track quality changes across model versions and prompt updates. Run the same test
          suite multiple times — EvalHub highlights score degradations automatically.
        </p>
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-sm text-zinc-500">Loading…</div>
      ) : !suites || suites.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center gap-3 py-20 text-center">
          <TrendingDown className="h-10 w-10 text-zinc-700" />
          <p className="text-sm font-medium text-zinc-400">No trend data yet</p>
          <p className="text-xs text-zinc-600 max-w-sm">
            Run the same test suite at least twice with any model. EvalHub will automatically
            detect quality regressions (≥10 percentage-point drop from peak).
          </p>
        </div>
      ) : (
        <>
          {/* Global regression banner */}
          {regressionCount > 0 && (
            <div className="rounded-lg border border-red-800/60 bg-red-900/20 px-4 py-3 flex items-center gap-3">
              <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
              <p className="text-sm text-red-300">
                <span className="font-semibold">{regressionCount}</span>{" "}
                {regressionCount === 1 ? "suite has" : "suites have"} detected regressions —
                pass rate dropped ≥10 pp below peak.
              </p>
            </div>
          )}

          {/* Suite cards */}
          <div className="space-y-4">
            {suites.map((suite) => (
              <SuiteCard key={suite.suite_id} suite={suite} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
