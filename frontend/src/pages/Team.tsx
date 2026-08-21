import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import * as invitesApi from "../api/invites";
import * as membersApi from "../api/members";
import type { Member, UserRole } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Layout } from "../components/Layout";

function skillsFromInput(value: string): string[] {
  return value
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
}

function MemberProfile({ member }: { member: Member }) {
  const queryClient = useQueryClient();
  const [fullName, setFullName] = useState(member.full_name ?? "");
  const [skillsInput, setSkillsInput] = useState(member.skills.join(", "));

  const save = useMutation({
    mutationFn: () => membersApi.updateMyProfile({ full_name: fullName, skills: skillsFromInput(skillsInput) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members"] }),
  });

  return (
    <div className="bg-slate-900 rounded-lg p-4 flex flex-col gap-3">
      <h3 className="font-semibold">Your profile</h3>
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Your name"
          className="flex-1 rounded bg-slate-800 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <input
          value={skillsInput}
          onChange={(e) => setSkillsInput(e.target.value)}
          placeholder="Skills, comma separated (e.g. react, python)"
          className="flex-1 rounded bg-slate-800 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <button
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-3 py-2 text-sm font-medium"
        >
          {save.isPending ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  );
}

function InvitePanel() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("member");
  const [lastLink, setLastLink] = useState<string | null>(null);

  const invitesQuery = useQuery({ queryKey: ["invites"], queryFn: invitesApi.listInvites });

  const create = useMutation({
    mutationFn: () => invitesApi.createInvite(email, role),
    onSuccess: (invite) => {
      setEmail("");
      setLastLink(invite.accept_url);
      queryClient.invalidateQueries({ queryKey: ["invites"] });
    },
  });

  const revoke = useMutation({
    mutationFn: (id: string) => invitesApi.revokeInvite(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invites"] }),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (email.trim()) create.mutate();
  }

  return (
    <div className="bg-slate-900 rounded-lg p-4 flex flex-col gap-3">
      <h3 className="font-semibold">Invite a teammate</h3>
      <p className="text-xs text-slate-500">
        There's no email sending yet - copy the link below and send it yourself.
      </p>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-2">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="teammate@company.com"
          className="flex-1 rounded bg-slate-800 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as UserRole)}
          className="rounded bg-slate-800 px-3 py-2 text-sm"
        >
          <option value="member">Member</option>
          <option value="admin">Admin</option>
        </select>
        <button
          disabled={create.isPending}
          className="rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-3 py-2 text-sm font-medium"
        >
          {create.isPending ? "Creating…" : "Create invite link"}
        </button>
      </form>
      {lastLink && (
        <p className="text-xs text-slate-400 break-all">
          Link ready: <span className="text-emerald-400">{lastLink}</span>
        </p>
      )}

      {invitesQuery.data && invitesQuery.data.length > 0 && (
        <div className="flex flex-col gap-1 pt-2 border-t border-slate-800">
          <p className="text-xs text-slate-500 mb-1">Pending invites</p>
          {invitesQuery.data.map((invite) => (
            <div key={invite.id} className="flex items-center justify-between text-sm bg-slate-800 rounded px-3 py-2">
              <span>
                {invite.email} <span className="text-slate-500">({invite.role})</span>
              </span>
              <button
                onClick={() => revoke.mutate(invite.id)}
                className="text-xs text-slate-400 hover:text-red-400"
              >
                Revoke
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MemberRow({ member, isSelf, isAdmin }: { member: Member; isSelf: boolean; isAdmin: boolean }) {
  const queryClient = useQueryClient();

  const setRole = useMutation({
    mutationFn: (role: UserRole) => membersApi.updateMember(member.id, { role }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members"] }),
  });
  const remove = useMutation({
    mutationFn: () => membersApi.removeMember(member.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members"] }),
  });

  return (
    <li className="bg-slate-900 rounded-lg p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium">
            {member.full_name || member.email} {isSelf && <span className="text-slate-500 text-xs">(you)</span>}
          </p>
          <p className="text-xs text-slate-500">{member.email}</p>
        </div>
        <div className="flex items-center gap-2">
          {isAdmin && !isSelf ? (
            <select
              value={member.role}
              onChange={(e) => setRole.mutate(e.target.value as UserRole)}
              className="rounded bg-slate-800 px-2 py-1 text-xs"
            >
              <option value="member">member</option>
              <option value="admin">admin</option>
            </select>
          ) : (
            <span className="text-xs rounded px-2 py-1 bg-slate-800 text-slate-300">{member.role}</span>
          )}
          {isAdmin && !isSelf && (
            <button onClick={() => remove.mutate()} className="text-xs text-slate-400 hover:text-red-400">
              Remove
            </button>
          )}
        </div>
      </div>

      {member.skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {member.skills.map((skill) => (
            <span key={skill} className="text-xs rounded-full bg-slate-800 px-2 py-0.5 text-slate-300">
              {skill}
            </span>
          ))}
        </div>
      )}

      {member.skill_stats.length > 0 && (
        <div className="flex flex-wrap gap-2 text-xs text-slate-500">
          {member.skill_stats.map((stat) => (
            <span key={stat.skill}>
              {stat.skill}: {stat.completed_task_count} task{stat.completed_task_count === 1 ? "" : "s"} ·{" "}
              {stat.completed_story_points} pts
            </span>
          ))}
        </div>
      )}
    </li>
  );
}

export default function TeamPage() {
  const { user } = useAuth();
  const membersQuery = useQuery({ queryKey: ["members"], queryFn: membersApi.listMembers });
  const isAdmin = user?.role === "admin";
  const me = membersQuery.data?.find((m) => m.id === user?.id);

  return (
    <Layout>
      <div className="flex flex-col gap-6">
        <h2 className="text-lg font-semibold">Team</h2>
        {me && <MemberProfile member={me} />}
        {isAdmin && <InvitePanel />}

        <div>
          <h3 className="font-semibold mb-3">Members</h3>
          <ul className="flex flex-col gap-2">
            {membersQuery.data?.map((member) => (
              <MemberRow key={member.id} member={member} isSelf={member.id === user?.id} isAdmin={isAdmin} />
            ))}
          </ul>
        </div>
      </div>
    </Layout>
  );
}
