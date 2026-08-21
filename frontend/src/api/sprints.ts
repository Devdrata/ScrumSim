import { apiClient } from "./client";
import type { Sprint } from "./types";

export async function listSprints(projectId: string): Promise<Sprint[]> {
  const { data } = await apiClient.get<Sprint[]>(`/projects/${projectId}/sprints`);
  return data;
}

export async function createSprint(
  projectId: string,
  input: { name: string; start_date?: string | null; end_date?: string | null; capacity_points?: number | null },
): Promise<Sprint> {
  const { data } = await apiClient.post<Sprint>(`/projects/${projectId}/sprints`, input);
  return data;
}

export async function updateSprint(sprintId: string, input: Partial<Sprint>): Promise<Sprint> {
  const { data } = await apiClient.patch<Sprint>(`/sprints/${sprintId}`, input);
  return data;
}
