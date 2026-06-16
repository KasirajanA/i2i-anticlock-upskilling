import type {
  ChangePasswordPayload,
  CreateTeamPayload,
  CreateUserPayload,
  PaginatedTeams,
  PaginatedUsers,
  Team,
  TeamDetail,
  UpdateProfilePayload,
  UpdateTeamPayload,
  UserProfile,
} from '../types/user'
import type { Role } from '../types/auth'

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const resp = await fetch(input, { credentials: 'include', ...init })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw Object.assign(new Error(body.detail ?? resp.statusText), { status: resp.status })
  }
  if (resp.status === 204) return undefined as T
  return resp.json() as Promise<T>
}

function json(body: unknown): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

// --- Users (admin) ---

export function listUsers(): Promise<PaginatedUsers> {
  return request('/api/v1/users')
}

export function createUser(payload: CreateUserPayload): Promise<UserProfile> {
  return request('/api/v1/users', json(payload))
}

export function updateUserRole(userId: number, role: Role): Promise<UserProfile> {
  return request(`/api/v1/users/${userId}/role`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role }),
  })
}

export function deactivateUser(userId: number): Promise<void> {
  return request(`/api/v1/users/${userId}/deactivate`, { method: 'POST' })
}

export function unlockUser(userId: number): Promise<void> {
  return request(`/api/v1/users/${userId}/unlock`, { method: 'POST' })
}

// --- Self-service profile ---

export function getMe(): Promise<UserProfile> {
  return request('/api/v1/users/me')
}

export function updateMe(payload: UpdateProfilePayload): Promise<UserProfile> {
  return request('/api/v1/users/me', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function uploadAvatar(file: File): Promise<{ avatar_url: string }> {
  const formData = new FormData()
  formData.append('file', file)
  return request('/api/v1/users/me/avatar', { method: 'POST', body: formData })
}

export function changePassword(payload: ChangePasswordPayload): Promise<void> {
  return request('/api/v1/users/me/change-password', json(payload))
}

// --- Teams ---

export function listTeams(): Promise<PaginatedTeams> {
  return request('/api/v1/teams')
}

export function createTeam(payload: CreateTeamPayload): Promise<TeamDetail> {
  return request('/api/v1/teams', json(payload))
}

export function getTeam(teamId: number): Promise<TeamDetail> {
  return request(`/api/v1/teams/${teamId}`)
}

export function updateTeam(teamId: number, payload: UpdateTeamPayload): Promise<TeamDetail> {
  return request(`/api/v1/teams/${teamId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function addMembers(teamId: number, userIds: number[]): Promise<void> {
  return request(`/api/v1/teams/${teamId}/members`, json({ user_ids: userIds }))
}

export function removeMember(teamId: number, userId: number): Promise<void> {
  return request(`/api/v1/teams/${teamId}/members/${userId}`, { method: 'DELETE' })
}
