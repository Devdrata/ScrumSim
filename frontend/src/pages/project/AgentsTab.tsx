import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import * as agentsApi from "../../api/agents";
import * as backlogApi from "../../api/backlog";
import * as membersApi from "../../api/members";
import * as sprintsApi from "../../api/sprints";
import type { AgentRun } from "../../api/types";

function extractError(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const detail = (err as any).response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "Agent run failed.";
}

interface SrsItemDraft {
  level: number;
  title: string;
  story_points?: number | null;
}

const SRS_LEVEL_STYLE: Record<number, string> = {
  1: "text-purple-300",
  2: "text-indigo-300",
  3: "text-slate-300",
};

function SrsTreePreview({ items }: { items: SrsItemDraft[] }) {
  return (
    <div className="text-sm flex flex-col gap-0.5">
      {items.map((item, i) => (
        <div key={i} style={{ marginLeft: (item.level - 1) * 16 }}>
          <span className={SRS_LEVEL_STYLE[item.level] ?? "text-slate-300"}>{item.title}</span>
          {item.story_points != null && <span className="text-slate-500 text-xs"> ({item.story_points} pts)</span>}
        </div>
      ))}
    </div>
  );
}

function ProposedOutput({ run, memberName, itemLabel }: { run: AgentRun; memberName: (id: string) => string; itemLabel: (id: string) => string }) {
  const output = run.proposed_output as Record<string, unknown>;

  if (run.agent_type === "planner") {
    const items =
      (output.recommended_items as { backlog_item_id: string; rationale: string; assignee_user_id?: string | null }[]) ?? [];
    return (
      <div className="text-sm">
        <p className="text-slate-300 mb-1">{String(output.summary ?? "")}</p>
        <ul className="flex flex-col gap-1 text-slate-400">
          {items.map((item, i) => (
            <li key={i}>
              <span className="text-slate-200">{itemLabel(item.backlog_item_id)}</span> — {item.rationale}
              {item.assignee_user_id && (
                <span className="text-emerald-400"> · assign to {memberName(item.assignee_user_id)}</span>
              )}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  if (run.agent_type === "standup") {
    const blockers = (output.blockers as string[]) ?? [];
    return (
      <div className="text-sm">
        <p className="text-slate-300">{String(output.summary ?? "")}</p>
        {blockers.length > 0 && (
          <p className="text-amber-400 mt-1">Blockers: {blockers.join("; ")}</p>
        )}
      </div>
    );
  }

  if (run.agent_type === "backlog") {
    return <p className="text-sm text-slate-300">{String(output.rationale ?? "")}</p>;
  }

  if (run.agent_type === "srs_intake") {
    return (
      <div className="text-sm flex flex-col gap-2">
        <p className="text-slate-300">{String(output.summary ?? "")}</p>
        <SrsTreePreview items={(output.items as SrsItemDraft[]) ?? []} />
      </div>
    );
  }

  // retro
  const wentWell = (output.went_well as string[]) ?? [];
  const wentWrong = (output.went_wrong as string[]) ?? [];
  const actionItems = (output.action_items as string[]) ?? [];
  return (
    <div className="text-sm grid grid-cols-1 sm:grid-cols-3 gap-2">
      <div>
        <p className="text-slate-500 mb-1">Went well</p>
        <ul className="list-disc list-inside text-slate-300">{wentWell.map((s, i) => <li key={i}>{s}</li>)}</ul>
      </div>
      <div>
        <p className="text-slate-500 mb-1">Went wrong</p>
        <ul className="list-disc list-inside text-slate-300">{wentWrong.map((s, i) => <li key={i}>{s}</li>)}</ul>
      </div>
      <div>
        <p className="text-slate-500 mb-1">Action items</p>
        <ul className="list-disc list-inside text-slate-300">{actionItems.map((s, i) => <li key={i}>{s}</li>)}</ul>
      </div>
    </div>
  );
}

export function AgentsTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [sprintId, setSprintId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sprintsQuery = useQuery({ queryKey: ["sprints", projectId], queryFn: () => sprintsApi.listSprints(projectId) });
  const runsQuery = useQuery({ queryKey: ["agentRuns", projectId], queryFn: () => agentsApi.listAgentRuns(projectId) });
  const membersQuery = useQuery({ queryKey: ["members"], queryFn: membersApi.listMembers });
  const backlogQuery = useQuery({ queryKey: ["backlog", projectId], queryFn: () => backlogApi.listBacklogItems(projectId) });

  function memberName(id: string): string {
    return membersQuery.data?.find((m) => m.id === id)?.full_name || membersQuery.data?.find((m) => m.id === id)?.email || "someone";
  }
  function itemLabel(id: string): string {
    return backlogQuery.data?.find((i) => i.id === id)?.title ?? id;
  }

  function invalidateRuns() {
    queryClient.invalidateQueries({ queryKey: ["agentRuns", projectId] });
  }

  const runPlanner = useMutation({
    mutationFn: () => agentsApi.runPlanner(projectId, sprintId),
    onSuccess: invalidateRuns,
    onError: (err) => setError(extractError(err)),
  });
  const runStandup = useMutation({
    mutationFn: () => agentsApi.runStandup(projectId),
    onSuccess: invalidateRuns,
    onError: (err) => setError(extractError(err)),
  });
  const runBacklog = useMutation({
    mutationFn: () => agentsApi.runBacklogAgent(projectId),
    onSuccess: invalidateRuns,
    onError: (err) => setError(extractError(err)),
  });
  const runRetro = useMutation({
    mutationFn: () => agentsApi.runRetro(sprintId),
    onSuccess: invalidateRuns,
    onError: (err) => setError(extractError(err)),
  });
  const runSrsIntake = useMutation({
    mutationFn: (file: File) => agentsApi.runSrsIntake(projectId, file),
    onSuccess: () => {
      invalidateRuns();
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    onError: (err) => setError(extractError(err)),
  });

  const approve = useMutation({
    mutationFn: (runId: string) => agentsApi.approveAgentRun(runId),
    onSuccess: () => {
      invalidateRuns();
      queryClient.invalidateQueries({ queryKey: ["backlog", projectId] });
      queryClient.invalidateQueries({ queryKey: ["backlogTree", projectId] });
      queryClient.invalidateQueries({ queryKey: ["standups", projectId] });
      queryClient.invalidateQueries({ queryKey: ["retro"] });
      queryClient.invalidateQueries({ queryKey: ["members"] });
    },
    onError: (err) => setError(extractError(err)),
  });
  const reject = useMutation({
    mutationFn: (runId: string) => agentsApi.rejectAgentRun(runId),
    onSuccess: invalidateRuns,
  });

  const anyRunning =
    runPlanner.isPending || runStandup.isPending || runBacklog.isPending || runRetro.isPending || runSrsIntake.isPending;

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-slate-900 rounded-lg p-4 flex flex-col gap-3">
        <h3 className="font-semibold">Run the Scrum Master agent</h3>
        <select
          value={sprintId}
          onChange={(e) => setSprintId(e.target.value)}
          className="rounded bg-slate-800 px-3 py-2 self-start text-sm"
        >
          <option value="">Select a sprint (needed for Planner / Retro)…</option>
          {sprintsQuery.data?.map((sprint) => (
            <option key={sprint.id} value={sprint.id}>
              {sprint.name}
            </option>
          ))}
        </select>
        <div className="flex flex-wrap gap-2">
          <button
            disabled={anyRunning || !sprintId}
            onClick={() => runPlanner.mutate()}
            className="rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 px-3 py-2 text-sm font-medium"
          >
            {runPlanner.isPending ? "Planning…" : "Sprint planner"}
          </button>
          <button
            disabled={anyRunning}
            onClick={() => runStandup.mutate()}
            className="rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 px-3 py-2 text-sm font-medium"
          >
            {runStandup.isPending ? "Summarizing…" : "Standup summary"}
          </button>
          <button
            disabled={anyRunning}
            onClick={() => runBacklog.mutate()}
            className="rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 px-3 py-2 text-sm font-medium"
          >
            {runBacklog.isPending ? "Prioritizing…" : "Backlog prioritizer"}
          </button>
          <button
            disabled={anyRunning || !sprintId}
            onClick={() => runRetro.mutate()}
            className="rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 px-3 py-2 text-sm font-medium"
          >
            {runRetro.isPending ? "Drafting…" : "Retro facilitator"}
          </button>
        </div>

        <div className="pt-2 border-t border-slate-800 flex flex-col gap-2">
          <p className="text-xs text-slate-500">
            Import an SRS document (.txt, .md, .pdf) and the agent will draft an epic/story/task tree from it.
          </p>
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.pdf"
              disabled={anyRunning}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) runSrsIntake.mutate(file);
              }}
              className="text-xs text-slate-400 file:mr-2 file:rounded file:border-0 file:bg-slate-800 file:px-3 file:py-1.5 file:text-slate-200"
            />
            {runSrsIntake.isPending && <span className="text-xs text-slate-500">Reading document…</span>}
          </div>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>

      <div className="flex flex-col gap-3">
        {runsQuery.data?.map((run) => (
          <div key={run.id} className="bg-slate-900 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium capitalize">{run.agent_type.replace("_", " ")} draft</span>
              <span
                className={`text-xs rounded px-2 py-1 ${
                  run.status === "pending"
                    ? "bg-amber-700 text-amber-100"
                    : run.status === "approved"
                      ? "bg-emerald-700 text-emerald-100"
                      : "bg-slate-700 text-slate-300"
                }`}
              >
                {run.status}
              </span>
            </div>
            <ProposedOutput run={run} memberName={memberName} itemLabel={itemLabel} />
            {run.status === "pending" && (
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => approve.mutate(run.id)}
                  className="rounded bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-xs font-medium"
                >
                  Approve
                </button>
                <button
                  onClick={() => reject.mutate(run.id)}
                  className="rounded bg-slate-700 hover:bg-slate-600 px-3 py-1.5 text-xs"
                >
                  Reject
                </button>
              </div>
            )}
          </div>
        ))}
        {runsQuery.data?.length === 0 && <p className="text-slate-500 text-sm">No agent runs yet.</p>}
      </div>
    </div>
  );
}
