import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createSegment, listSegments } from '../services/contactApi';

export function useSegmentList(entity_type: string) {
  return useQuery({
    queryKey: ['segments', entity_type],
    queryFn: () => listSegments(entity_type),
    staleTime: 60_000,
  });
}

export function useCreateSegment(entity_type: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createSegment,
    onSettled: () => qc.invalidateQueries({ queryKey: ['segments', entity_type] }),
  });
}
