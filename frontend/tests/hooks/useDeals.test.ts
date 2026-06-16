import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { createElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useDeals } from '../../src/hooks/useDeals'
import type { DealListResponse } from '../../src/types/deal'

vi.mock('../../src/services/dealService', () => ({
  listDeals: vi.fn(),
}))

import { listDeals } from '../../src/services/dealService'
const mockList = listDeals as ReturnType<typeof vi.fn>

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return createElement(QueryClientProvider, { client: qc }, children)
}

describe('useDeals', () => {
  it('returns paginated list from the service', async () => {
    const mockData: DealListResponse = {
      total: 2,
      page: 1,
      limit: 25,
      items: [
        {
          id: 1,
          ref_id: 'DEAL-0001',
          title: 'Deal A',
          value: '1000.00',
          stage: 'Lead In',
          expected_close_date: '2026-12-31',
          is_overdue: false,
          owner: { id: 1, name: 'Alice', email: 'a@b.com' },
          account: { id: 1, name: 'Acme' },
        },
        {
          id: 2,
          ref_id: 'DEAL-0002',
          title: 'Deal B',
          value: '2000.00',
          stage: 'Qualified',
          expected_close_date: '2026-12-31',
          is_overdue: false,
          owner: { id: 1, name: 'Alice', email: 'a@b.com' },
          account: { id: 1, name: 'Acme' },
        },
      ],
    }
    mockList.mockResolvedValue(mockData)

    const { result } = renderHook(() => useDeals(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.total).toBe(2)
    expect(result.current.data?.items).toHaveLength(2)
    expect(mockList).toHaveBeenCalledWith({})
  })

  it('passes filter params to the service', async () => {
    mockList.mockResolvedValue({ total: 0, page: 1, limit: 25, items: [] })

    const { result } = renderHook(
      () => useDeals({ stage: 'Qualified', owner_id: 5 }),
      { wrapper },
    )
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockList).toHaveBeenCalledWith(
      expect.objectContaining({ stage: 'Qualified', owner_id: 5 }),
    )
  })
})
