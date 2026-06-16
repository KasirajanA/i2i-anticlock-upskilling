import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { createElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useStageChange } from '../../src/hooks/useStageChange'
import { DEALS_KEY } from '../../src/hooks/useDeals'
import type { DealListResponse } from '../../src/types/deal'

vi.mock('../../src/services/dealService', () => ({
  changeDealStage: vi.fn(),
  listDeals: vi.fn(),
}))

import { changeDealStage } from '../../src/services/dealService'
const mockChange = changeDealStage as ReturnType<typeof vi.fn>

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: qc }, children)
  }
}

const seedData: DealListResponse = {
  total: 1,
  page: 1,
  limit: 25,
  items: [
    {
      id: 1,
      ref_id: 'DEAL-0001',
      title: 'Test Deal',
      value: '1000.00',
      stage: 'Lead In',
      expected_close_date: '2026-12-31',
      is_overdue: false,
      owner: { id: 1, name: 'Alice', email: 'a@b.com' },
      account: { id: 1, name: 'Acme' },
    },
  ],
}

describe('useStageChange', () => {
  it('optimistic update moves deal to target stage immediately', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    qc.setQueryData([DEALS_KEY, {}], seedData)

    mockChange.mockResolvedValue({
      ref_id: 'DEAL-0001',
      previous_stage: 'Lead In',
      new_stage: 'Qualified',
      is_overdue: false,
      updated_at: '2026-06-16T00:00:00Z',
    })

    const { result } = renderHook(() => useStageChange(), { wrapper: makeWrapper(qc) })

    act(() => {
      result.current.mutate({ refId: 'DEAL-0001', payload: { stage: 'Qualified' } })
    })

    await waitFor(() => {
      const cached = qc.getQueryData<DealListResponse>([DEALS_KEY, {}])
      expect(cached?.items[0].stage).toBe('Qualified')
    })
  })

  it('rolls back optimistic update on API error', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    qc.setQueryData([DEALS_KEY, {}], seedData)

    mockChange.mockRejectedValue(Object.assign(new Error('Terminal stage'), { status: 422 }))

    const { result } = renderHook(() => useStageChange(), { wrapper: makeWrapper(qc) })

    act(() => {
      result.current.mutate({ refId: 'DEAL-0001', payload: { stage: 'Qualified' } })
    })

    await waitFor(() => result.current.isError)

    const cached = qc.getQueryData<DealListResponse>([DEALS_KEY, {}])
    expect(cached?.items[0].stage).toBe('Lead In')
  })
})
