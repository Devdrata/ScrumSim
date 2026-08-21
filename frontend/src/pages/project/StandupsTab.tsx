import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import * as standupsApi from "../../api/standups";

export function StandupsTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [content, setContent] = useState("");
  const [blockers, setBlockers] = useState("");

  const entriesQuery = useQuery({
    queryKey: ["standups", projectId],
    queryFn: () => standupsApi.listStandupEntries(projectId),
  });

  const createEntry = useMutation({
    mutationFn: () => standupsApi.createStandupEntry(projectId, { content, blockers: blockers || undefined }),
    onSuccess: () => {
      setContent("");
      setBlockers("");
      queryClient.invalidateQueries({ queryKey: ["standups", projectId] });
    },
  });

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (content.trim()) createEntry.mutate();
        }}
        className="flex flex-col gap-2 bg-slate-900 rounded p-3"
      >
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="What did you work on?"
          rows={2}
          className="rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <input
          value={blockers}
          onChange={(e) => setBlockers(e.target.value)}
          placeholder="Any blockers? (optional)"
          className="rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <button className="self-start rounded bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-medium">
          Post update
        </button>
      </form>

      <ul className="flex flex-col gap-2">
        {entriesQuery.data?.map((entry) => (
          <li key={entry.id} className="rounded bg-slate-900 px-3 py-2">
            <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
              <span className={entry.author === "agent" ? "text-emerald-400" : ""}>
                {entry.author === "agent" ? "ScrumSim agent" : "team member"}
              </span>
              <span>{new Date(entry.created_at).toLocaleString()}</span>
            </div>
            <p>{entry.content}</p>
            {entry.blockers && <p className="text-amber-400 text-sm mt-1">Blocker: {entry.blockers}</p>}
          </li>
        ))}
        {entriesQuery.data?.length === 0 && <p className="text-slate-500 text-sm">No standup updates yet.</p>}
      </ul>
    </div>
  );
}
