import { apiClient } from "./client";
import type { AssignedItem, Member, UserRole } from "./types";

export async function listMembers(): Promise<Member[]> {
  const { data } = await apiClient.get<Member[]>("/members");
  return data;
}

export async function updateMyProfile(input: { full_name?: string; skills?: string[] }): Promise<Member> {
  const { data } = await apiClient.patch<Member>("/members/me", input);
  return data;
}

export async function updateMember(
  userId: string,
  input: { full_name?: string; skills?: string[]; role?: UserRole },
): Promise<Member> {
  const { data } = await apiClient.patch<Member>(`/members/${userId}`, input);
  return data;
}

export async function removeMember(userId: string): Promise<void> {
  await apiClient.delete(`/members/${userId}`);
}

export async function listMyAssignedItems(): Promise<AssignedItem[]> {
  const { data } = await apiClient.get<AssignedItem[]>("/me/assigned-items");
  return data;
}
