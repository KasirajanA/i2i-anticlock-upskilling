import type { Role } from './auth'

export interface UserProfile {
  id: number
  name: string
  email: string
  role: Role
  is_active: boolean
  display_name: string | null
  avatar_url: string | null
  timezone: string | null
  created_at: string
}

export interface TeamMember {
  user_id: number
  joined_at: string
}

export interface Team {
  id: number
  name: string
  lead_user_id: number | null
  created_by_id: number
  created_at: string
  member_count: number
}

export interface TeamDetail extends Team {
  members: TeamMember[]
}

export interface PaginatedUsers {
  items: UserProfile[]
  total: number
}

export interface PaginatedTeams {
  items: Team[]
  total: number
}

export interface CreateUserPayload {
  name: string
  email: string
  role: Role
  password: string
}

export interface UpdateProfilePayload {
  display_name?: string | null
  timezone?: string | null
}

export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}

export interface CreateTeamPayload {
  name: string
  lead_user_id?: number | null
  member_ids: number[]
}

export interface UpdateTeamPayload {
  name?: string | null
  lead_user_id?: number | null
}
