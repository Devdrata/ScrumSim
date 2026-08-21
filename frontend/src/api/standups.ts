import { apiClient } from "./client";
import type { StandupEntry } from "./types";

export async function listStandupEntries(projectId: string): Promise<StandupEntry[]> {
  const { data } = await apiClient.get<StandupEntry[]>(`/projects/${projectId}/standups`);
  return data;
}

export async function createStandupEntry(
  projectId: string,
  input: { content: string; blockers?: string; sprint_id?: string | null },
): Promise<StandupEntry> {
  const { data } = await apiClient.post<StandupEntry>(`/projects/${projectId}/standups`, input);
  return data;
}
