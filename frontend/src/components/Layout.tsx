import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import * as membersApi from "../api/members";
import { useAuth } from "../auth/AuthContext";

function useOverdueCount(): number {
  const { user } = useAuth();
  const itemsQuery = useQuery({
    queryKey: ["myAssignedItems"],
    queryFn: membersApi.listMyAssignedItems,
    enabled: !!user,
    refetchInterval: 60_000,
  });
  const today = new Date().toISOString().slice(0, 10);
  return (itemsQuery.data ?? []).filter((item) => item.deadline && item.status !== "done" && item.deadline < today)
    .length;
}

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const overdueCount = useOverdueCount();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <Link to="/" className="font-semibold text-lg">
          ScrumSim
        </Link>
        <div className="flex items-center gap-4 text-sm text-slate-400">
          <Link to="/me" className="hover:text-slate-100 flex items-center gap-1.5">
            My Work
            {overdueCount > 0 && (
              <span
                className="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-red-600 text-white text-[10px] font-semibold"
                title={`${overdueCount} task${overdueCount === 1 ? "" : "s"} past deadline`}
              >
                {overdueCount}
              </span>
            )}
          </Link>
          <Link to="/team" className="hover:text-slate-100">
            Team
          </Link>
          <Link to="/settings/integrations" className="hover:text-slate-100">
            Integrations
          </Link>
          <span>{user?.email}</span>
          <button onClick={logout} className="text-slate-400 hover:text-slate-100">
            Log out
          </button>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
