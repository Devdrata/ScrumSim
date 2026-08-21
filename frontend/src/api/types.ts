export type UserRole = "admin" | "member";

export interface User {
  id: string;
  org_id: string;
  email: string;
  role: UserRole;
}

export interface Team {
  id: string;
  org_id: string;
  name: string;
  created_at: string;
}

export interface Project {
  id: string;
  team_id: string;
  name: string;
  created_at: string;
}

export type SprintStatus = "planned" | "active" | "completed";

export interface Sprint {
  id: string;
  project_id: string;
  name: string;
  start_date: string | null;
  end_date: string | null;
  status: SprintStatus;
  capacity_points: number | null;
  created_at: string;
}

export type BacklogItemStatus = "backlog" | "in_sprint" | "in_progress" | "done";
export type BacklogItemType = "epic" | "story" | "task" | "subtask";

export interface BacklogItem {
  id: string;
  project_id: string;
  sprint_id: string | null;
  parent_id: string | null;
  assignee_id: string | null;
  title: string;
  description: string | null;
  status: BacklogItemStatus;
  item_type: BacklogItemType;
  impact_score: number | null;
  deadline: string | null;
  priority_rank: number | null;
  story_points: number | null;
  required_skills: string[];
  acceptance_criteria: string | null;
  created_at: string;
  updated_at: string;
}

export interface BacklogTreeNode extends BacklogItem {
  children: BacklogTreeNode[];
}

export type StandupAuthor = "agent" | "user";

export interface StandupEntry {
  id: string;
  project_id: string;
  sprint_id: string | null;
  author: StandupAuthor;
  content: string;
  blockers: string | null;
  created_at: string;
}

export type RetroCategory = "went_well" | "went_wrong" | "action_item";

export interface RetroEntry {
  id: string;
  sprint_id: string;
  category: RetroCategory;
  content: string;
  created_by: string | null;
  created_at: string;
}

export type IntegrationProvider = "github" | "jira" | "slack";

export type AgentType = "planner" | "standup" | "backlog" | "retro" | "srs_intake";
export type AgentRunStatus = "pending" | "approved" | "rejected" | "edited";

export interface AgentRun {
  id: string;
  org_id: string;
  project_id: string | null;
  agent_type: AgentType;
  input_context: Record<string, unknown>;
  proposed_output: Record<string, unknown>;
  status: AgentRunStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface SkillStat {
  skill: string;
  completed_task_count: number;
  completed_story_points: number;
}

export interface Member {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  skills: string[];
  skill_stats: SkillStat[];
}

export interface AssignedItem {
  id: string;
  project_id: string;
  project_name: string;
  title: string;
  item_type: BacklogItemType;
  status: BacklogItemStatus;
  story_points: number | null;
  deadline: string | null;
  updated_at: string;
}

export type InviteStatus = "pending" | "accepted" | "revoked";

export interface Invite {
  id: string;
  email: string;
  role: UserRole;
  status: InviteStatus;
  accept_url: string;
  created_at: string;
}

export interface InvitePreview {
  org_name: string;
  email: string;
}
