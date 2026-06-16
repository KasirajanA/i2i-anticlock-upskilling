import { create } from 'zustand'
import type { DealStage } from '../types/deal'

interface PipelineFilters {
  stage: DealStage | undefined
  owner_id: number | undefined
  account_id: number | undefined
  is_overdue: boolean | undefined
  close_date_from: string | undefined
  close_date_to: string | undefined
  setStage: (stage: DealStage | undefined) => void
  setOwnerId: (id: number | undefined) => void
  setAccountId: (id: number | undefined) => void
  setIsOverdue: (v: boolean | undefined) => void
  setCloseDateFrom: (d: string | undefined) => void
  setCloseDateTo: (d: string | undefined) => void
  reset: () => void
}

const initialFilters = {
  stage: undefined,
  owner_id: undefined,
  account_id: undefined,
  is_overdue: undefined,
  close_date_from: undefined,
  close_date_to: undefined,
}

export const usePipelineFilters = create<PipelineFilters>((set) => ({
  ...initialFilters,
  setStage: (stage) => set({ stage }),
  setOwnerId: (owner_id) => set({ owner_id }),
  setAccountId: (account_id) => set({ account_id }),
  setIsOverdue: (is_overdue) => set({ is_overdue }),
  setCloseDateFrom: (close_date_from) => set({ close_date_from }),
  setCloseDateTo: (close_date_to) => set({ close_date_to }),
  reset: () => set(initialFilters),
}))
