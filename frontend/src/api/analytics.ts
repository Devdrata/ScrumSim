import { apiClient } from "./client";

export interface BurndownPoint {
  date: string;
  remaining_points: number;
}

export interface SprintBurndown {
  sprint_id: string;
  sprint_name: string;
  status: string;
  total_items: number;
  completed_items: number;
  completion_rate: number | null;
  capacity_points: number | null;
  total_points: number;
  completed_points: number;
  burndown_series: BurndownPoint[];
}

export interface BottleneckItem {
  id: string;
  title: string;
  status: string;
  days_in_status: number;
  sprint_id: string | null;
}

export interface ProjectAnalytics {
  active_sprint: SprintBurndown | null;
  bottlenecks: BottleneckItem[];
  velocity: number | null;
}

export async function getProjectAnalytics(projectId: string): Promise<ProjectAnalytics> {
  const { data } = await apiClient.get<ProjectAnalytics>(`/projects/${projectId}/analytics`);
  return data;
}
