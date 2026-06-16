import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  createDeal,
  getDeal,
  listDeals,
  updateDeal,
} from '../services/dealService'
import type {
  DealCreateRequest,
  DealFilterParams,
  DealUpdateRequest,
} from '../types/deal'

export const DEALS_KEY = 'deals'

export function useDeals(filters: DealFilterParams = {}) {
  return useQuery({
    queryKey: [DEALS_KEY, filters],
    queryFn: () => listDeals(filters),
  })
}

export function useDeal(refId: string) {
  return useQuery({
    queryKey: [DEALS_KEY, refId],
    queryFn: () => getDeal(refId),
    enabled: Boolean(refId),
  })
}

export function useCreateDeal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: DealCreateRequest) => createDeal(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [DEALS_KEY] })
    },
  })
}

export function usePatchDeal(refId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: DealUpdateRequest) => updateDeal(refId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [DEALS_KEY] })
    },
  })
}
