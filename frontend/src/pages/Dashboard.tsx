import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import * as teamsApi from "../api/teams";
import { useAuth } from "../auth/AuthContext";
import { Layout } from "../components/Layout";

export default function Dashboard() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const queryClient = useQueryClient();
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
  const [newTeamName, setNewTeamName] = useState("");
  const [newProjectName, setNewProjectName] = useState("");

  const teamsQuery = useQuery({ queryKey: ["teams"], queryFn: teamsApi.listTeams });
  const projectsQuery = useQuery({
    queryKey: ["projects", selectedTeamId],
    queryFn: () => teamsApi.listProjects(selectedTeamId!),
    enabled: !!selectedTeamId,
  });

  const createTeam = useMutation({
    mutationFn: () => teamsApi.createTeam(newTeamName),
    onSuccess: (team) => {
      setNewTeamName("");
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      setSelectedTeamId(team.id);
    },
  });

  const createProject = useMutation({
    mutationFn: () => teamsApi.createProject(selectedTeamId!, newProjectName),
    onSuccess: () => {
      setNewProjectName("");
      queryClient.invalidateQueries({ queryKey: ["projects", selectedTeamId] });
    },
  });

  return (
    <Layout>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <section>
          <h2 className="text-lg font-semibold mb-3">Teams</h2>
          <ul className="flex flex-col gap-2 mb-4">
            {teamsQuery.data?.map((team) => (
              <li key={team.id}>
                <button
                  onClick={() => setSelectedTeamId(team.id)}
                  className={`w-full text-left rounded px-3 py-2 ${
                    selectedTeamId === team.id ? "bg-emerald-600" : "bg-slate-900 hover:bg-slate-800"
                  }`}
                >
                  {team.name}
                </button>
              </li>
            ))}
            {teamsQuery.data?.length === 0 && <p className="text-slate-500 text-sm">No teams yet.</p>}
          </ul>
          {isAdmin && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (newTeamName.trim()) createTeam.mutate();
              }}
              className="flex gap-2"
            >
              <input
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                placeholder="New team name"
                className="flex-1 rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <button className="rounded bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-medium">
                Add team
              </button>
            </form>
          )}
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-3">Projects</h2>
          {!selectedTeamId && <p className="text-slate-500 text-sm">Select a team to see its projects.</p>}
          {selectedTeamId && (
            <>
              <ul className="flex flex-col gap-2 mb-4">
                {projectsQuery.data?.map((project) => (
                  <li key={project.id}>
                    <Link
                      to={`/projects/${project.id}`}
                      className="block rounded bg-slate-900 hover:bg-slate-800 px-3 py-2"
                    >
                      {project.name}
                    </Link>
                  </li>
                ))}
                {projectsQuery.data?.length === 0 && (
                  <p className="text-slate-500 text-sm">No projects yet.</p>
                )}
              </ul>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (newProjectName.trim()) createProject.mutate();
                }}
                className="flex gap-2"
              >
                <input
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="New project name"
                  className="flex-1 rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
                />
                <button className="rounded bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-sm font-medium">
                  Add project
                </button>
              </form>
            </>
          )}
        </section>
      </div>
    </Layout>
  );
}
