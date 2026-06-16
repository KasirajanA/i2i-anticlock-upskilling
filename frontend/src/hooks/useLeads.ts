import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { convertLead, createLead, getLead, listLeads, updateLead } from '../services/contactApi';
import type { LeadFilters } from '../types/contact';

export function useLeadList(filters: LeadFilters = {}) {
  return useInfiniteQuery({
    queryKey: ['leads', filters],
    queryFn: () => listLeads(filters),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
    staleTime: 30_000,
  });
}

export function useLead(id: number) {
  return useQuery({
    queryKey: ['leads', id],
    queryFn: () => getLead(id),
    enabled: id > 0,
  });
}

export function useCreateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createLead,
    onSettled: () => qc.invalidateQueries({ queryKey: ['leads'] }),
  });
}

export function useUpdateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: Parameters<typeof updateLead>[1] }) =>
      updateLead(id, body),
    onSettled: () => qc.invalidateQueries({ queryKey: ['leads'] }),
  });
}

export function useConvertLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: Parameters<typeof convertLead>[1] }) =>
      convertLead(id, body),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['leads'] });
      qc.invalidateQueries({ queryKey: ['contacts'] });
    },
  });
}
