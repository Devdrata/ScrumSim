import { apiClient } from "./client";
import type { TokenResponse } from "./auth";
import type { Invite, InvitePreview, UserRole } from "./types";

export async function createInvite(email: string, role: UserRole): Promise<Invite> {
  const { data } = await apiClient.post<Invite>("/invites", { email, role });
  return data;
}

export async function listInvites(): Promise<Invite[]> {
  const { data } = await apiClient.get<Invite[]>("/invites");
  return data;
}

export async function revokeInvite(inviteId: string): Promise<void> {
  await apiClient.delete(`/invites/${inviteId}`);
}

export async function previewInvite(token: string): Promise<InvitePreview> {
  const { data } = await apiClient.get<InvitePreview>(`/invites/${token}`);
  return data;
}

export async function acceptInvite(token: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>(`/invites/${token}/accept`, { password });
  return data;
}
