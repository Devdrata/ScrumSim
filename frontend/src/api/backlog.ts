import { apiClient } from "./client";
import type { BacklogItem, BacklogItemType, BacklogTreeNode } from "./types";

export interface BacklogItemInput {
  title: string;
  description?: string;
  impact_score?: number;
  deadline?: string | null;
  item_type?: BacklogItemType;
  parent_id?: string | null;
  story_points?: number | null;
  required_skills?: string[];
  acceptance_criteria?: string | null;
  assignee_id?: string | null;
}

export async function listBacklogItems(projectId: string): Promise<BacklogItem[]> {
  const { data } = await apiClient.get<BacklogItem[]>(`/projects/${projectId}/backlog`);
  return data;
}

export async function getBacklogTree(projectId: string): Promise<BacklogTreeNode[]> {
  const { data } = await apiClient.get<BacklogTreeNode[]>(`/projects/${projectId}/backlog/tree`);
  return data;
}

export async function createBacklogItem(projectId: string, input: BacklogItemInput): Promise<BacklogItem> {
  const { data } = await apiClient.post<BacklogItem>(`/projects/${projectId}/backlog`, input);
  return data;
}

export async function updateBacklogItem(itemId: string, input: Partial<BacklogItemInput & BacklogItem>): Promise<BacklogItem> {
  const { data } = await apiClient.patch<BacklogItem>(`/backlog/${itemId}`, input);
  return data;
}
