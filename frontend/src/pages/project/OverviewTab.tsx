import { useQuery } from "@tanstack/react-query";

import * as analyticsApi from "../../api/analytics";
import type { BurndownPoint } from "../../api/analytics";

const CHART_WIDTH = 480;
const CHART_HEIGHT = 140;
const PADDING = 8;

function BurndownChart({
  series,
  startingPoints,
  hasItems,
}: {
  series: BurndownPoint[];
  startingPoints: number;
  hasItems: boolean;
}) {
  if (!hasItems) {
    return <p className="text-slate-500 text-sm">No items in this sprint yet.</p>;
  }
  if (series.length < 2) {
    return <p className="text-slate-500 text-sm">Sprint just started — the trend line appears once a day has passed.</p>;
  }

  const maxValue = Math.max(startingPoints, ...series.map((p) => p.remaining_points), 1);
  const innerWidth = CHART_WIDTH - PADDING * 2;
  const innerHeight = CHART_HEIGHT - PADDING * 2;

  const toXY = (index: number, value: number) => {
    const x = PADDING + (index / (series.length - 1)) * innerWidth;
    const y = PADDING + innerHeight - (value / maxValue) * innerHeight;
    return [x, y] as const;
  };

  const actualPoints = series.map((p, i) => toXY(i, p.remaining_points).join(",")).join(" ");
  const [idealStartX, idealStartY] = toXY(0, startingPoints);
  const [idealEndX, idealEndY] = toXY(series.length - 1, 0);

  return (
    <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} className="w-full h-36">
      <line
        x1={idealStartX}
        y1={idealStartY}
        x2={idealEndX}
        y2={idealEndY}
        stroke="currentColor"
        className="text-slate-700"
        strokeDasharray="4 4"
        strokeWidth={1.5}
      />
      <polyline points={actualPoints} fill="none" stroke="currentColor" className="text-emerald-500" strokeWidth={2} />
      {series.map((p, i) => {
        const [x, y] = toXY(i, p.remaining_points);
        return <circle key={p.date} cx={x} cy={y} r={2.5} className="fill-emerald-400" />;
      })}
    </svg>
  );
}

export function OverviewTab({ projectId }: { projectId: string }) {
  const analyticsQuery = useQuery({
    queryKey: ["analytics", projectId],
    queryFn: () => analyticsApi.getProjectAnalytics(projectId),
  });

  const data = analyticsQuery.data;
  const sprint = data?.active_sprint;

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-slate-900 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Active sprint burndown</h3>
          {data?.velocity != null && (
            <span className="text-xs text-slate-500">Recent velocity: {data.velocity} pts/sprint</span>
          )}
        </div>
        {!sprint && <p className="text-slate-500 text-sm">No active sprint.</p>}
        {sprint && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-sm">
              <span>{sprint.sprint_name}</span>
              <span className="text-slate-400">
                {sprint.completed_points} / {sprint.total_points} pts
                {sprint.capacity_points != null && <> · capacity {sprint.capacity_points}</>}
              </span>
            </div>
            <BurndownChart
              series={sprint.burndown_series}
              startingPoints={sprint.capacity_points ?? sprint.total_points}
              hasItems={sprint.total_items > 0}
            />
            <div className="w-full h-2 rounded bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-emerald-500"
                style={{ width: `${(sprint.completion_rate ?? 0) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      <div className="bg-slate-900 rounded-lg p-4">
        <h3 className="font-semibold mb-3">Bottlenecks</h3>
        <p className="text-xs text-slate-500 mb-3">Backlog items stuck "in progress" for 3+ days.</p>
        {data?.bottlenecks.length === 0 && <p className="text-slate-500 text-sm">No bottlenecks detected.</p>}
        <ul className="flex flex-col gap-2">
          {data?.bottlenecks.map((item) => (
            <li key={item.id} className="flex items-center justify-between bg-slate-800 rounded px-3 py-2 text-sm">
              <span>{item.title}</span>
              <span className="text-amber-400">{item.days_in_status.toFixed(1)}d in progress</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
