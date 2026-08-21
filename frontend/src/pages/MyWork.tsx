import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import * as membersApi from "../api/members";
import type { AssignedItem } from "../api/types";
import { Layout } from "../components/Layout";

const STATUS_STYLES: Record<string, string> = {
  backlog: "bg-slate-700 text-slate-200",
  in_sprint: "bg-indigo-700 text-indigo-100",
  in_progress: "bg-amber-700 text-amber-100",
  done: "bg-emerald-700 text-emerald-100",
};

function isOverdue(item: AssignedItem): boolean {
  if (!item.deadline || item.status === "done") return false;
  return item.deadline < new Date().toISOString().slice(0, 10);
}

function groupByProject(items: AssignedItem[]): Map<string, AssignedItem[]> {
  const groups = new Map<string, AssignedItem[]>();
  for (const item of items) {
    const key = item.project_name;
    const list = groups.get(key) ?? [];
    list.push(item);
    groups.set(key, list);
  }
  return groups;
}

export default function MyWork() {
  const itemsQuery = useQuery({ queryKey: ["myAssignedItems"], queryFn: membersApi.listMyAssignedItems });
  const items = itemsQuery.data ?? [];
  const overdueItems = items.filter(isOverdue);
  const groups = groupByProject(items);

  return (
    <Layout>
      <div className="flex flex-col gap-6">
        <h2 className="text-lg font-semibold">My work</h2>

        {overdueItems.length > 0 && (
          <div className="rounded-lg border border-red-800 bg-red-950/60 px-4 py-3">
            <p className="text-sm font-medium text-red-300">
              ⚠ {overdueItems.length} task{overdueItems.length === 1 ? "" : "s"} past deadline
            </p>
            <ul className="mt-2 flex flex-col gap-1">
              {overdueItems.map((item) => (
                <li key={item.id} className="text-xs text-red-200/90 flex items-center justify-between">
                  <span>
                    {item.title} <span className="text-red-400/80">({item.project_name})</span>
                  </span>
                  <span className="text-red-400">was due {item.deadline}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {items.length === 0 && <p className="text-slate-500 text-sm">Nothing assigned to you yet.</p>}
        {[...groups.entries()].map(([projectName, projectItems]) => (
          <div key={projectName}>
            <Link
              to={`/projects/${projectItems[0].project_id}`}
              className="text-sm font-medium text-slate-300 hover:text-emerald-400"
            >
              {projectName}
            </Link>
            <ul className="flex flex-col gap-2 mt-2">
              {projectItems.map((item) => {
                const overdue = isOverdue(item);
                return (
                  <li
                    key={item.id}
                    className={`flex items-center justify-between bg-slate-900 rounded-lg px-4 py-3 text-sm ${
                      overdue ? "border border-red-800" : ""
                    }`}
                  >
                    <div>
                      <span className="text-slate-500 uppercase text-xs mr-2">{item.item_type}</span>
                      {item.title}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      {item.story_points != null && <span>{item.story_points} pts</span>}
                      {item.deadline && (
                        <span className={overdue ? "text-red-400 font-medium" : ""}>
                          {overdue ? "⚠ due" : "due"} {item.deadline}
                        </span>
                      )}
                      <span className={`rounded px-2 py-1 ${STATUS_STYLES[item.status] ?? ""}`}>{item.status}</span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </Layout>
  );
}
