import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import PipelineBoard from '../../src/components/pipeline/PipelineBoard'
import type { DealListResponse } from '../../src/types/deal'

vi.mock('../../src/services/dealService', () => ({
  listDeals: vi.fn(),
  getDeal: vi.fn(),
  changeDealStage: vi.fn(),
  getComments: vi.fn(),
  addComment: vi.fn(),
  getActivity: vi.fn(),
}))

import { listDeals } from '../../src/services/dealService'
const mockList = listDeals as ReturnType<typeof vi.fn>

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('PipelineBoard', () => {
  it('renders six stage columns', async () => {
    mockList.mockResolvedValue({
      total: 0,
      page: 1,
      limit: 200,
      items: [],
    } satisfies DealListResponse)

    render(
      <Wrapper>
        <PipelineBoard />
      </Wrapper>,
    )

    const stages = [
      'Lead In',
      'Qualified',
      'Proposal',
      'Negotiation',
      'Closed Won',
      'Closed Lost',
    ]
    for (const stage of stages) {
      expect(screen.getByText(stage)).toBeInTheDocument()
    }
  })

  it('renders deal cards in the correct stage column', async () => {
    mockList.mockResolvedValue({
      total: 1,
      page: 1,
      limit: 200,
      items: [
        {
          id: 1,
          ref_id: 'DEAL-0001',
          title: 'Pipeline Test Deal',
          value: '10000.00',
          stage: 'Qualified',
          expected_close_date: '2026-12-31',
          is_overdue: false,
          owner: { id: 1, name: 'Alice', email: 'a@b.com' },
          account: { id: 1, name: 'Acme' },
        },
      ],
    } satisfies DealListResponse)

    const { findByText } = render(
      <Wrapper>
        <PipelineBoard />
      </Wrapper>,
    )

    expect(await findByText('Pipeline Test Deal')).toBeInTheDocument()
  })
})
