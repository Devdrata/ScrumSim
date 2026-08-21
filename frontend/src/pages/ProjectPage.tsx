import { useState } from "react";
import { useParams } from "react-router-dom";

import { Layout } from "../components/Layout";
import { AgentsTab } from "./project/AgentsTab";
import { BoardTab } from "./project/BoardTab";
import { OverviewTab } from "./project/OverviewTab";
import { RetroTab } from "./project/RetroTab";
import { SprintsTab } from "./project/SprintsTab";
import { StandupsTab } from "./project/StandupsTab";

const TABS = ["Overview", "Board", "Sprints", "Standups", "Retro", "Agents"] as const;
type Tab = (typeof TABS)[number];

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [tab, setTab] = useState<Tab>("Overview");

  if (!projectId) return null;

  return (
    <Layout>
      <div className="flex gap-2 border-b border-slate-800 mb-6">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === t ? "border-emerald-500 text-emerald-400" : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview" && <OverviewTab projectId={projectId} />}
      {tab === "Board" && <BoardTab projectId={projectId} />}
      {tab === "Sprints" && <SprintsTab projectId={projectId} />}
      {tab === "Standups" && <StandupsTab projectId={projectId} />}
      {tab === "Retro" && <RetroTab projectId={projectId} />}
      {tab === "Agents" && <AgentsTab projectId={projectId} />}
    </Layout>
  );
}
