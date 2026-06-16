import { useMutation, useQueryClient } from '@tanstack/react-query'
import { changeDealStage } from '../services/dealService'
import type { DealListResponse, DealStage, StageChangeRequest } from '../types/deal'
import { DEALS_KEY } from './useDeals'

interface StageChangeMutationArgs {
  refId: string
  payload: StageChangeRequest
}

export function useStageChange() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ refId, payload }: StageChangeMutationArgs) =>
      changeDealStage(refId, payload),

    onMutate: async ({ refId, payload }) => {
      await qc.cancelQueries({ queryKey: [DEALS_KEY] })

      const previousQueries = qc.getQueriesData<DealListResponse>({
        queryKey: [DEALS_KEY],
      })

      qc.setQueriesData<DealListResponse>({ queryKey: [DEALS_KEY] }, (old) => {
        if (!old) return old
        return {
          ...old,
          items: old.items.map((item) =>
            item.ref_id === refId
              ? { ...item, stage: payload.stage as DealStage }
              : item,
          ),
        }
      })

      return { previousQueries }
    },

    onError: (_err, _vars, context) => {
      if (context?.previousQueries) {
        for (const [queryKey, data] of context.previousQueries) {
          qc.setQueryData(queryKey, data)
        }
      }
    },

    onSettled: () => {
      qc.invalidateQueries({ queryKey: [DEALS_KEY] })
    },
  })
}
