import { apiClient } from "./client";
import type { RetroCategory, RetroEntry } from "./types";

export async function listRetroEntries(sprintId: string): Promise<RetroEntry[]> {
  const { data } = await apiClient.get<RetroEntry[]>(`/sprints/${sprintId}/retro`);
  return data;
}

export async function createRetroEntry(
  sprintId: string,
  input: { category: RetroCategory; content: string },
): Promise<RetroEntry> {
  const { data } = await apiClient.post<RetroEntry>(`/sprints/${sprintId}/retro`, input);
  return data;
}
