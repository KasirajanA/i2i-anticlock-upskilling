import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '../services/userApi'
import type { CreateUserPayload, UpdateProfilePayload } from '../types/user'
import type { Role } from '../types/auth'

const USER_STALE = 2 * 60 * 1000

export function useUserList() {
  return useQuery({
    queryKey: ['users'],
    queryFn: api.listUsers,
    staleTime: USER_STALE,
  })
}

export function useMe() {
  return useQuery({
    queryKey: ['users', 'me'],
    queryFn: api.getMe,
    staleTime: USER_STALE,
  })
}

export function useCreateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateUserPayload) => api.createUser(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })
}

export function useUpdateUserRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: Role }) =>
      api.updateUserRole(userId, role),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })
}

export function useDeactivateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (userId: number) => api.deactivateUser(userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })
}

export function useUpdateMe() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateProfilePayload) => api.updateMe(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users', 'me'] }),
  })
}

export function useUploadAvatar() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => api.uploadAvatar(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users', 'me'] }),
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (payload: { current_password: string; new_password: string }) =>
      api.changePassword(payload),
  })
}
