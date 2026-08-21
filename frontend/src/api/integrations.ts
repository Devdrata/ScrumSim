import { apiClient } from "./client";
import type { IntegrationProvider } from "./types";

export interface IntegrationStatus {
  provider: IntegrationProvider;
  connected: boolean;
  configured_at: string | null;
  detail: Record<string, unknown> | null;
}

export async function listIntegrations(): Promise<IntegrationStatus[]> {
  const { data } = await apiClient.get<IntegrationStatus[]>("/integrations");
  return data;
}

export async function testIntegration(
  provider: IntegrationProvider,
  payload: Record<string, string>,
): Promise<IntegrationStatus> {
  const { data } = await apiClient.post<IntegrationStatus>(`/integrations/${provider}/test`, payload);
  return data;
}

export async function saveIntegration(
  provider: IntegrationProvider,
  payload: Record<string, string>,
): Promise<IntegrationStatus> {
  const { data } = await apiClient.post<IntegrationStatus>(`/integrations/${provider}`, payload);
  return data;
}

export async function deleteIntegration(provider: IntegrationProvider): Promise<void> {
  await apiClient.delete(`/integrations/${provider}`);
}
