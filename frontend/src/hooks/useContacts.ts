import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  archiveContact,
  createContact,
  getContact,
  listContacts,
  updateContact,
} from '../services/contactApi';
import type { ContactFilters } from '../types/contact';

export function useContactList(filters: ContactFilters = {}) {
  return useInfiniteQuery({
    queryKey: ['contacts', filters],
    queryFn: ({ pageParam }) =>
      listContacts({ ...filters, cursor: pageParam as string | undefined }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
    staleTime: 30_000,
  });
}

export function useContact(id: number) {
  return useQuery({
    queryKey: ['contacts', id],
    queryFn: () => getContact(id),
    enabled: id > 0,
  });
}

export function useCreateContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createContact,
    onSettled: () => qc.invalidateQueries({ queryKey: ['contacts'] }),
  });
}

export function useUpdateContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: Parameters<typeof updateContact>[1] }) =>
      updateContact(id, body),
    onSettled: () => qc.invalidateQueries({ queryKey: ['contacts'] }),
  });
}

export function useArchiveContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: archiveContact,
    onSettled: () => qc.invalidateQueries({ queryKey: ['contacts'] }),
  });
}
