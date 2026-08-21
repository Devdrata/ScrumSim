import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import * as retrosApi from "../../api/retros";
import * as sprintsApi from "../../api/sprints";
import type { RetroCategory } from "../../api/types";

const CATEGORIES: { key: RetroCategory; label: string }[] = [
  { key: "went_well", label: "Went well" },
  { key: "went_wrong", label: "Went wrong" },
  { key: "action_item", label: "Action items" },
];

export function RetroTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [sprintId, setSprintId] = useState<string>("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState<RetroCategory>("went_well");

  const sprintsQuery = useQuery({ queryKey: ["sprints", projectId], queryFn: () => sprintsApi.listSprints(projectId) });
  const entriesQuery = useQuery({
    queryKey: ["retro", sprintId],
    queryFn: () => retrosApi.listRetroEntries(sprintId),
    enabled: !!sprintId,
  });

  const createEntry = useMutation({
    mutationFn: () => retrosApi.createRetroEntry(sprintId, { category, content }),
    onSuccess: () => {
      setContent("");
      queryClient.invalidateQueries({ queryKey: ["retro", sprintId] });
    },
  });

  return (
    <div className="flex flex-col gap-4">
      <select
        value={sprintId}
        onChange={(e) => setSprintId(e.target.value)}
        className="rounded bg-slate-800 px-3 py-2 self-start"
      >
        <option value="">Select a sprint…</option>
        {sprintsQuery.data?.map((sprint) => (
          <option key={sprint.id} value={sprint.id}>
            {sprint.name}
          </option>
        ))}
      </select>

      {sprintId && (
        <>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (content.trim()) createEntry.mutate();
            }}
            className="flex gap-2"
          >
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as RetroCategory)}
              className="rounded bg-slate-800 px-2 py-2"
            >
              {CATEGORIES.map((c) => (
                <option key={c.key} value={c.key}>
                  {c.label}
                </option>
              ))}
            </select>
            <input
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Add a note"
              className="flex-1 rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <button className="rounded bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-medium">Add</button>
          </form>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {CATEGORIES.map((c) => (
              <div key={c.key} className="bg-slate-900 rounded p-3">
                <h3 className="font-medium mb-2">{c.label}</h3>
                <ul className="flex flex-col gap-2 text-sm">
                  {entriesQuery.data
                    ?.filter((entry) => entry.category === c.key)
                    .map((entry) => (
                      <li key={entry.id} className="bg-slate-800 rounded px-2 py-1">
                        {entry.content}
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
