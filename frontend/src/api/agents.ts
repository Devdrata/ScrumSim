import { apiClient } from "./client";
import type { AgentRun } from "./types";

export async function runPlanner(projectId: string, sprintId: string): Promise<AgentRun> {
  const { data } = await apiClient.post<AgentRun>("/agents/planner/run", {
    project_id: projectId,
    sprint_id: sprintId,
  });
  return data;
}

export async function runStandup(projectId: string): Promise<AgentRun> {
  const { data } = await apiClient.post<AgentRun>("/agents/standup/run", { project_id: projectId });
  return data;
}

export async function runBacklogAgent(projectId: string): Promise<AgentRun> {
  const { data } = await apiClient.post<AgentRun>("/agents/backlog/run", { project_id: projectId });
  return data;
}

export async function runRetro(sprintId: string): Promise<AgentRun> {
  const { data } = await apiClient.post<AgentRun>("/agents/retro/run", { sprint_id: sprintId });
  return data;
}

export async function runSrsIntake(projectId: string, file: File): Promise<AgentRun> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<AgentRun>(`/agents/srs-intake/run/${projectId}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listAgentRuns(projectId: string): Promise<AgentRun[]> {
  const { data } = await apiClient.get<AgentRun[]>("/agents/runs", { params: { project_id: projectId } });
  return data;
}

export async function approveAgentRun(runId: string): Promise<AgentRun> {
  const { data } = await apiClient.post<AgentRun>(`/agents/runs/${runId}/approve`);
  return data;
}

export async function rejectAgentRun(runId: string): Promise<AgentRun> {
  const { data } = await apiClient.post<AgentRun>(`/agents/runs/${runId}/reject`);
  return data;
}
