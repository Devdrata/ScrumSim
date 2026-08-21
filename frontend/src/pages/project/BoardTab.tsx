import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import * as backlogApi from "../../api/backlog";
import * as membersApi from "../../api/members";
import type { BacklogItemStatus, BacklogItemType, BacklogTreeNode } from "../../api/types";

const COLUMNS: { status: BacklogItemStatus; label: string }[] = [
  { status: "backlog", label: "Backlog" },
  { status: "in_sprint", label: "In Sprint" },
  { status: "in_progress", label: "In Progress" },
  { status: "done", label: "Done" },
];

const TYPE_BADGE: Record<BacklogItemType, string> = {
  epic: "bg-purple-800 text-purple-100",
  story: "bg-indigo-800 text-indigo-100",
  task: "bg-slate-700 text-slate-200",
  subtask: "bg-slate-800 text-slate-400",
};

// Same status→hue mapping used across the app (MyWork, Sprints) so a status reads the
// same color everywhere: neutral for backlog, blue while queued, amber mid-flight, green done.
const STATUS_BORDER: Record<BacklogItemStatus, string> = {
  backlog: "border-slate-600",
  in_sprint: "border-indigo-500",
  in_progress: "border-amber-500",
  done: "border-emerald-500",
};

const STATUS_SELECT: Record<BacklogItemStatus, string> = {
  backlog: "bg-slate-900 text-slate-300",
  in_sprint: "bg-indigo-950 text-indigo-300",
  in_progress: "bg-amber-950 text-amber-300",
  done: "bg-emerald-950 text-emerald-300",
};

const STATUS_DOT: Record<BacklogItemStatus, string> = {
  backlog: "bg-slate-500",
  in_sprint: "bg-indigo-500",
  in_progress: "bg-amber-500",
  done: "bg-emerald-500",
};

function countDescendants(node: BacklogTreeNode): number {
  return node.children.reduce((sum, child) => sum + 1 + countDescendants(child), 0);
}

function isOverdue(node: BacklogTreeNode): boolean {
  if (!node.deadline || node.status === "done") return false;
  return node.deadline < new Date().toISOString().slice(0, 10);
}

function TaskCard({
  node,
  depth,
  memberName,
  onDragStart,
  onStatusChange,
  onAssigneeChange,
  onDeadlineChange,
  memberOptions,
}: {
  node: BacklogTreeNode;
  depth: number;
  memberName: (id: string | null) => string;
  onDragStart: (id: string) => void;
  onStatusChange: (id: string, status: BacklogItemStatus) => void;
  onAssigneeChange: (id: string, assigneeId: string | null) => void;
  onDeadlineChange: (id: string, deadline: string | null) => void;
  memberOptions: { id: string; label: string }[];
}) {
  const [expanded, setExpanded] = useState(true);
  const childCount = countDescendants(node);
  const overdue = isOverdue(node);

  return (
    <div style={{ marginLeft: depth * 12 }}>
      <div
        draggable={depth === 0}
        onDragStart={() => onDragStart(node.id)}
        className={`bg-slate-800 rounded-lg p-3 text-sm flex flex-col gap-2 border-l-4 ${
          depth === 0 ? "cursor-grab" : ""
        } ${overdue ? "border-red-500" : STATUS_BORDER[node.status]}`}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className={`text-[10px] uppercase rounded px-1.5 py-0.5 shrink-0 ${TYPE_BADGE[node.item_type]}`}>
              {node.item_type}
            </span>
            <span className="truncate">{node.title}</span>
            {overdue && (
              <span className="text-[10px] rounded px-1.5 py-0.5 shrink-0 bg-red-950 text-red-300 border border-red-800">
                ⚠ overdue
              </span>
            )}
          </div>
          {node.children.length > 0 && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="text-xs text-slate-500 hover:text-slate-300 shrink-0"
            >
              {expanded ? "▾" : "▸"} {childCount}
            </button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
          {node.story_points != null && <span>{node.story_points} pts</span>}
          <select
            value={node.assignee_id ?? ""}
            onChange={(e) => onAssigneeChange(node.id, e.target.value || null)}
            className="rounded bg-slate-900 px-1.5 py-0.5 text-xs"
          >
            <option value="">unassigned</option>
            {memberOptions.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
          <select
            value={node.status}
            onChange={(e) => onStatusChange(node.id, e.target.value as BacklogItemStatus)}
            className={`rounded px-1.5 py-0.5 text-xs font-medium ${STATUS_SELECT[node.status]}`}
          >
            {COLUMNS.map((c) => (
              <option key={c.status} value={c.status}>
                {c.label}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={node.deadline ?? ""}
            onChange={(e) => onDeadlineChange(node.id, e.target.value || null)}
            title="Deadline"
            className={`rounded bg-slate-900 px-1.5 py-0.5 text-xs ${overdue ? "text-red-400" : ""}`}
          />
        </div>

        {node.required_skills.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {node.required_skills.map((skill) => (
              <span key={skill} className="text-[10px] rounded-full bg-slate-900 px-2 py-0.5 text-slate-400">
                {skill}
              </span>
            ))}
          </div>
        )}
        {node.assignee_id && (
          <p className="text-xs text-slate-500">assigned to {memberName(node.assignee_id)}</p>
        )}
      </div>

      {expanded &&
        node.children.map((child) => (
          <div key={child.id} className="mt-2">
            <TaskCard
              node={child}
              depth={depth + 1}
              memberName={memberName}
              onDragStart={onDragStart}
              onStatusChange={onStatusChange}
              onAssigneeChange={onAssigneeChange}
              onDeadlineChange={onDeadlineChange}
              memberOptions={memberOptions}
            />
          </div>
        ))}
    </div>
  );
}

export function BoardTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [itemType, setItemType] = useState<BacklogItemType>("task");
  const [parentId, setParentId] = useState("");
  const [deadline, setDeadline] = useState("");
  const [draggingId, setDraggingId] = useState<string | null>(null);

  const treeQuery = useQuery({ queryKey: ["backlogTree", projectId], queryFn: () => backlogApi.getBacklogTree(projectId) });
  const flatQuery = useQuery({ queryKey: ["backlog", projectId], queryFn: () => backlogApi.listBacklogItems(projectId) });
  const membersQuery = useQuery({ queryKey: ["members"], queryFn: membersApi.listMembers });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["backlogTree", projectId] });
    queryClient.invalidateQueries({ queryKey: ["backlog", projectId] });
    queryClient.invalidateQueries({ queryKey: ["members"] });
  }

  const createItem = useMutation({
    mutationFn: () =>
      backlogApi.createBacklogItem(projectId, {
        title,
        item_type: itemType,
        parent_id: parentId || null,
        deadline: deadline || null,
      }),
    onSuccess: () => {
      setTitle("");
      setDeadline("");
      invalidate();
    },
  });

  const updateItem = useMutation({
    mutationFn: (vars: {
      id: string;
      patch: Partial<{ status: BacklogItemStatus; assignee_id: string | null; deadline: string | null }>;
    }) => backlogApi.updateBacklogItem(vars.id, vars.patch),
    onSuccess: invalidate,
  });

  const memberOptions = (membersQuery.data ?? []).map((m) => ({ id: m.id, label: m.full_name || m.email }));
  function memberName(id: string | null): string {
    if (!id) return "";
    return memberOptions.find((m) => m.id === id)?.label ?? "someone";
  }

  const tree = treeQuery.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (title.trim()) createItem.mutate();
        }}
        className="flex flex-wrap gap-2"
      >
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New item title"
          className="flex-1 min-w-[200px] rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <select
          value={itemType}
          onChange={(e) => setItemType(e.target.value as BacklogItemType)}
          className="rounded bg-slate-800 px-3 py-2 text-sm"
        >
          <option value="epic">Epic</option>
          <option value="story">Story</option>
          <option value="task">Task</option>
          <option value="subtask">Subtask</option>
        </select>
        <select value={parentId} onChange={(e) => setParentId(e.target.value)} className="rounded bg-slate-800 px-3 py-2 text-sm">
          <option value="">No parent</option>
          {flatQuery.data?.map((item) => (
            <option key={item.id} value={item.id}>
              {item.title}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
          title="Deadline (optional)"
          className="rounded bg-slate-800 px-3 py-2 text-sm"
        />
        <button className="rounded bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-medium">Add item</button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {COLUMNS.map((column) => {
          const roots = tree.filter((node) => node.status === column.status);
          return (
            <div
              key={column.status}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => {
                if (draggingId) updateItem.mutate({ id: draggingId, patch: { status: column.status } });
                setDraggingId(null);
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg p-3 flex flex-col gap-2 min-h-[200px]"
            >
              <div className="flex items-center justify-between text-xs text-slate-500 font-medium uppercase">
                <span className="flex items-center gap-1.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[column.status]}`} />
                  {column.label}
                </span>
                <span>{roots.length}</span>
              </div>
              {roots.map((node) => (
                <TaskCard
                  key={node.id}
                  node={node}
                  depth={0}
                  memberName={memberName}
                  onDragStart={setDraggingId}
                  onStatusChange={(id, status) => updateItem.mutate({ id, patch: { status } })}
                  onAssigneeChange={(id, assigneeId) => updateItem.mutate({ id, patch: { assignee_id: assigneeId } })}
                  onDeadlineChange={(id, deadlineValue) => updateItem.mutate({ id, patch: { deadline: deadlineValue } })}
                  memberOptions={memberOptions}
                />
              ))}
            </div>
          );
        })}
      </div>
      {tree.length === 0 && <p className="text-slate-500 text-sm">No backlog items yet.</p>}
    </div>
  );
}
