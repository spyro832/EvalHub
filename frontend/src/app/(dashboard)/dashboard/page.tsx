"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, Clock, DollarSign, FlaskConical, TrendingUp, Zap } from "lucide-react";
import { costApi, evaluationsApi, modelsApi, testSuitesApi } from "@/lib/api";
import { formatCost, formatTokens } from "@/lib/utils";

function StatCard({
  label,
  value,
  icon: Icon,
  sub,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  sub?: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-400">{label}</p>
        <Icon className="h-4 w-4 text-zinc-600" />
      </div>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      {sub && <p className="mt-1 text-xs text-zinc-500">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const { data: cost } = useQuery({ queryKey: ["cost-summary"], queryFn: costApi.summary });
  const { data: evaluations } = useQuery({
    queryKey: ["evaluations"],
    queryFn: evaluationsApi.list,
  });
  const { data: models } = useQuery({ queryKey: ["models"], queryFn: modelsApi.list });
  const { data: suites } = useQuery({ queryKey: ["test-suites"], queryFn: testSuitesApi.list });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Overview of your AI evaluations, costs, and models.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          label="Total Spent"
          value={cost ? formatCost(cost.total_usd) : "—"}
          icon={DollarSign}
          sub={`${cost?.total_calls ?? 0} API calls`}
        />
        <StatCard
          label="Evaluations"
          value={String(evaluations?.length ?? 0)}
          icon={BarChart3}
          sub="all time"
        />
        <StatCard
          label="Models Configured"
          value={String(models?.length ?? 0)}
          icon={Zap}
          sub="active"
        />
        <StatCard
          label="Test Suites"
          value={String(suites?.length ?? 0)}
          icon={FlaskConical}
          sub="defined"
        />
      </div>

      {/* Tokens */}
      {cost && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <StatCard
            label="Input Tokens"
            value={formatTokens(cost.total_input_tokens)}
            icon={TrendingUp}
          />
          <StatCard
            label="Output Tokens"
            value={formatTokens(cost.total_output_tokens)}
            icon={TrendingUp}
          />
          <StatCard
            label="Total Tokens"
            value={formatTokens(cost.total_input_tokens + cost.total_output_tokens)}
            icon={Clock}
          />
        </div>
      )}

      {/* Recent evaluations */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900">
        <div className="border-b border-zinc-800 px-5 py-3">
          <h2 className="text-sm font-medium text-white">Recent Evaluations</h2>
        </div>
        {!evaluations || evaluations.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-zinc-500">
            No evaluations yet. Go to{" "}
            <a href="/evaluations" className="text-indigo-400 hover:underline">
              Compare
            </a>{" "}
            to run your first one.
          </div>
        ) : (
          <ul className="divide-y divide-zinc-800">
            {evaluations.slice(0, 5).map((ev) => (
              <li key={ev.id} className="flex items-center gap-4 px-5 py-3">
                <span
                  className={`h-2 w-2 rounded-full ${
                    ev.status === "completed"
                      ? "bg-green-500"
                      : ev.status === "failed"
                        ? "bg-red-500"
                        : "bg-yellow-500"
                  }`}
                />
                <span className="flex-1 truncate text-sm text-zinc-300">
                  {ev.name ?? ev.prompt.slice(0, 80)}
                </span>
                <span className="text-xs text-zinc-500">
                  {new Date(ev.created_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
