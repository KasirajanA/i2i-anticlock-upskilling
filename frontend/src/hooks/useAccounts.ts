import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  archiveAccount,
  createAccount,
  getAccount,
  getAccountTimeline,
  listAccounts,
  updateAccount,
} from '../services/contactApi';
import type { AccountFilters } from '../types/contact';

export function useAccountList(filters: AccountFilters = {}) {
  return useInfiniteQuery({
    queryKey: ['accounts', filters],
    queryFn: ({ pageParam }) =>
      listAccounts({ ...filters, cursor: pageParam as string | undefined }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
    staleTime: 30_000,
  });
}

export function useAccount(id: number) {
  return useQuery({
    queryKey: ['accounts', id],
    queryFn: () => getAccount(id),
    enabled: id > 0,
  });
}

export function useAccountTimeline(id: number) {
  return useQuery({
    queryKey: ['accounts', id, 'timeline'],
    queryFn: () => getAccountTimeline(id),
    enabled: id > 0,
  });
}

export function useCreateAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createAccount,
    onSettled: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  });
}

export function useUpdateAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: Parameters<typeof updateAccount>[1] }) =>
      updateAccount(id, body),
    onSettled: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  });
}

export function useArchiveAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: archiveAccount,
    onSettled: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  });
}
