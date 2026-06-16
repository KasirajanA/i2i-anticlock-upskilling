import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '../services/userApi'
import type { CreateTeamPayload, UpdateTeamPayload } from '../types/user'

const TEAM_STALE = 2 * 60 * 1000

export function useTeamList() {
  return useQuery({
    queryKey: ['teams'],
    queryFn: api.listTeams,
    staleTime: TEAM_STALE,
  })
}

export function useTeam(id: number) {
  return useQuery({
    queryKey: ['teams', id],
    queryFn: () => api.getTeam(id),
    staleTime: TEAM_STALE,
    enabled: !!id,
  })
}

export function useCreateTeam() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateTeamPayload) => api.createTeam(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['teams'] }),
  })
}

export function useUpdateTeam() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ teamId, payload }: { teamId: number; payload: UpdateTeamPayload }) =>
      api.updateTeam(teamId, payload),
    onSuccess: (_data, { teamId }) => {
      qc.invalidateQueries({ queryKey: ['teams'] })
      qc.invalidateQueries({ queryKey: ['teams', teamId] })
    },
  })
}

export function useAddMembers() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ teamId, userIds }: { teamId: number; userIds: number[] }) =>
      api.addMembers(teamId, userIds),
    onSuccess: (_data, { teamId }) => qc.invalidateQueries({ queryKey: ['teams', teamId] }),
  })
}

export function useRemoveMember() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ teamId, userId }: { teamId: number; userId: number }) =>
      api.removeMember(teamId, userId),
    onSuccess: (_data, { teamId }) => qc.invalidateQueries({ queryKey: ['teams', teamId] }),
  })
}
