import { apiClient } from "./client";
import type { User } from "./types";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function signup(orgName: string, email: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/signup", {
    org_name: orgName,
    email,
    password,
  });
  return data;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  return data;
}

export async function me(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}
