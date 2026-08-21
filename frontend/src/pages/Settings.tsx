import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import * as integrationsApi from "../api/integrations";
import type { IntegrationProvider } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Layout } from "../components/Layout";

interface FieldConfig {
  key: string;
  label: string;
  placeholder?: string;
  type?: string;
}

const PROVIDER_CONFIG: Record<IntegrationProvider, { label: string; fields: FieldConfig[]; help: string }> = {
  github: {
    label: "GitHub",
    help: "Fine-grained personal access token with read access to Contents/Pull requests/Issues. See SETUP.md.",
    fields: [
      { key: "token", label: "Personal access token", type: "password" },
      { key: "repo", label: "Repository", placeholder: "owner/repo" },
    ],
  },
  jira: {
    label: "Jira",
    help: "Atlassian API token generated at id.atlassian.com. See SETUP.md.",
    fields: [
      { key: "site_url", label: "Site URL", placeholder: "https://yourteam.atlassian.net" },
      { key: "email", label: "Atlassian account email" },
      { key: "api_token", label: "API token", type: "password" },
      { key: "project_key", label: "Project key", placeholder: "PROJ" },
    ],
  },
  slack: {
    label: "Slack",
    help: "Bot User OAuth Token from a Slack App with chat:write + channels:read scopes. See SETUP.md.",
    fields: [
      { key: "bot_token", label: "Bot token", placeholder: "xoxb-…", type: "password" },
      { key: "channel", label: "Channel", placeholder: "#standups" },
    ],
  },
};

function IntegrationCard({
  provider,
  connected,
  canDisconnect,
}: {
  provider: IntegrationProvider;
  connected: boolean;
  canDisconnect: boolean;
}) {
  const queryClient = useQueryClient();
  const config = PROVIDER_CONFIG[provider];
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(config.fields.map((f) => [f.key, ""])),
  );
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  const testMutation = useMutation({
    mutationFn: () => integrationsApi.testIntegration(provider, values),
    onSuccess: () => setMessage({ kind: "success", text: "Connection succeeded." }),
    onError: (err) => setMessage({ kind: "error", text: extractError(err) }),
  });

  const saveMutation = useMutation({
    mutationFn: () => integrationsApi.saveIntegration(provider, values),
    onSuccess: () => {
      setMessage({ kind: "success", text: "Saved." });
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
    onError: (err) => setMessage({ kind: "error", text: extractError(err) }),
  });

  const deleteMutation = useMutation({
    mutationFn: () => integrationsApi.deleteIntegration(provider),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integrations"] }),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    saveMutation.mutate();
  }

  return (
    <form onSubmit={onSubmit} className="bg-slate-900 rounded-lg p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{config.label}</h3>
        <span
          className={`text-xs rounded px-2 py-1 ${connected ? "bg-emerald-700 text-emerald-100" : "bg-slate-700 text-slate-300"}`}
        >
          {connected ? "connected" : "not connected"}
        </span>
      </div>
      <p className="text-xs text-slate-500">{config.help}</p>

      {config.fields.map((field) => (
        <input
          key={field.key}
          type={field.type ?? "text"}
          placeholder={field.placeholder ?? field.label}
          value={values[field.key]}
          onChange={(e) => setValues((v) => ({ ...v, [field.key]: e.target.value }))}
          className="rounded bg-slate-800 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        />
      ))}

      {message && (
        <p className={`text-sm ${message.kind === "success" ? "text-emerald-400" : "text-red-400"}`}>
          {message.text}
        </p>
      )}

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => testMutation.mutate()}
          disabled={testMutation.isPending}
          className="rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-50 px-3 py-2 text-sm"
        >
          {testMutation.isPending ? "Testing…" : "Test connection"}
        </button>
        <button
          type="submit"
          disabled={saveMutation.isPending}
          className="rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-3 py-2 text-sm font-medium"
        >
          {saveMutation.isPending ? "Saving…" : "Save"}
        </button>
        {connected && canDisconnect && (
          <button
            type="button"
            onClick={() => deleteMutation.mutate()}
            className="ml-auto rounded bg-red-900 hover:bg-red-800 px-3 py-2 text-sm"
          >
            Disconnect
          </button>
        )}
      </div>
    </form>
  );
}

function extractError(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const detail = (err as any).response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "Something went wrong.";
}

export default function Settings() {
  const { user } = useAuth();
  const integrationsQuery = useQuery({ queryKey: ["integrations"], queryFn: integrationsApi.listIntegrations });

  const connectedByProvider = Object.fromEntries(
    (integrationsQuery.data ?? []).map((i) => [i.provider, i.connected]),
  ) as Record<IntegrationProvider, boolean>;

  return (
    <Layout>
      <h1 className="text-xl font-semibold mb-6">Integrations</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {(Object.keys(PROVIDER_CONFIG) as IntegrationProvider[]).map((provider) => (
          <IntegrationCard
            key={provider}
            provider={provider}
            connected={!!connectedByProvider[provider]}
            canDisconnect={user?.role === "admin"}
          />
        ))}
      </div>
    </Layout>
  );
}
