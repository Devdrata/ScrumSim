import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import * as sprintsApi from "../../api/sprints";
import type { SprintStatus } from "../../api/types";

const STATUS_STYLES: Record<SprintStatus, string> = {
  planned: "bg-slate-700 text-slate-200",
  active: "bg-emerald-700 text-emerald-100",
  completed: "bg-indigo-700 text-indigo-100",
};

export function SprintsTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [capacityPoints, setCapacityPoints] = useState("");

  const sprintsQuery = useQuery({ queryKey: ["sprints", projectId], queryFn: () => sprintsApi.listSprints(projectId) });

  const createSprint = useMutation({
    mutationFn: () =>
      sprintsApi.createSprint(projectId, {
        name,
        capacity_points: capacityPoints ? Number(capacityPoints) : null,
      }),
    onSuccess: () => {
      setName("");
      setCapacityPoints("");
      queryClient.invalidateQueries({ queryKey: ["sprints", projectId] });
    },
  });

  const setStatus = useMutation({
    mutationFn: (vars: { id: string; status: SprintStatus }) => sprintsApi.updateSprint(vars.id, { status: vars.status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sprints", projectId] }),
  });

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) createSprint.mutate();
        }}
        className="flex gap-2"
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New sprint name (e.g. Sprint 12)"
          className="flex-1 rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <input
          value={capacityPoints}
          onChange={(e) => setCapacityPoints(e.target.value)}
          type="number"
          min={0}
          placeholder="Capacity (pts)"
          className="w-36 rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <button className="rounded bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-medium">
          Add sprint
        </button>
      </form>

      <ul className="flex flex-col gap-2">
        {sprintsQuery.data?.map((sprint) => (
          <li key={sprint.id} className="flex items-center justify-between rounded bg-slate-900 px-3 py-2">
            <span>
              {sprint.name}
              {sprint.capacity_points != null && (
                <span className="text-slate-500 text-xs ml-2">cap {sprint.capacity_points}pts</span>
              )}
            </span>
            <div className="flex items-center gap-2">
              <span className={`text-xs rounded px-2 py-1 ${STATUS_STYLES[sprint.status]}`}>{sprint.status}</span>
              {sprint.status !== "active" && (
                <button
                  onClick={() => setStatus.mutate({ id: sprint.id, status: "active" })}
                  className="text-xs text-emerald-400 hover:underline"
                >
                  Start
                </button>
              )}
              {sprint.status !== "completed" && (
                <button
                  onClick={() => setStatus.mutate({ id: sprint.id, status: "completed" })}
                  className="text-xs text-slate-400 hover:underline"
                >
                  Complete
                </button>
              )}
            </div>
          </li>
        ))}
        {sprintsQuery.data?.length === 0 && <p className="text-slate-500 text-sm">No sprints yet.</p>}
      </ul>
    </div>
  );
}
