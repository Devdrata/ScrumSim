import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";

import * as invitesApi from "../api/invites";
import { useAuth } from "../auth/AuthContext";

export default function AcceptInvite() {
  const { token } = useParams<{ token: string }>();
  const { setSession } = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const previewQuery = useQuery({
    queryKey: ["invitePreview", token],
    queryFn: () => invitesApi.previewInvite(token!),
    enabled: !!token,
    retry: false,
  });

  if (!token) return <Navigate to="/login" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await invitesApi.acceptInvite(token!, password);
      setSession(res.access_token, res.user);
      navigate("/");
    } catch (err) {
      const message =
        err && typeof err === "object" && "response" in err
          ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
            ((err as any).response?.data?.detail ?? "Could not accept invite.")
          : "Could not accept invite.";
      setError(String(message));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
      <div className="w-full max-w-sm bg-slate-900 rounded-lg p-6 flex flex-col gap-4">
        {previewQuery.isLoading && <p className="text-slate-400 text-sm">Loading invite…</p>}
        {previewQuery.isError && (
          <p className="text-sm text-red-400">This invite link is invalid or no longer valid.</p>
        )}
        {previewQuery.data && (
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div>
              <h1 className="text-xl font-semibold">Join {previewQuery.data.org_name} on ScrumSim</h1>
              <p className="text-sm text-slate-400 mt-1">
                Set a password for <span className="text-slate-200">{previewQuery.data.email}</span>
              </p>
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <input
              type="password"
              placeholder="Password (min 8 characters)"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <button
              type="submit"
              disabled={submitting}
              className="rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-3 py-2 font-medium"
            >
              {submitting ? "Joining…" : "Join organization"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
