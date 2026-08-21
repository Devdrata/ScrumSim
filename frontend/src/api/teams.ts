import { apiClient } from "./client";
import type { Member, Project, Team } from "./types";

export async function listTeams(): Promise<Team[]> {
  const { data } = await apiClient.get<Team[]>("/teams");
  return data;
}

export async function createTeam(name: string): Promise<Team> {
  const { data } = await apiClient.post<Team>("/teams", { name });
  return data;
}

export async function listProjects(teamId: string): Promise<Project[]> {
  const { data } = await apiClient.get<Project[]>(`/teams/${teamId}/projects`);
  return data;
}

export async function createProject(teamId: string, name: string): Promise<Project> {
  const { data } = await apiClient.post<Project>(`/teams/${teamId}/projects`, { name });
  return data;
}

export async function listTeamMembers(teamId: string): Promise<Member[]> {
  const { data } = await apiClient.get<Member[]>(`/teams/${teamId}/members`);
  return data;
}

export async function addTeamMember(teamId: string, userId: string): Promise<Member> {
  const { data } = await apiClient.post<Member>(`/teams/${teamId}/members`, { user_id: userId });
  return data;
}

export async function removeTeamMember(teamId: string, userId: string): Promise<void> {
  await apiClient.delete(`/teams/${teamId}/members/${userId}`);
}
