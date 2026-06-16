import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import ContractList from '../src/components/contracts/ContractList'
import type { ContractListResponse } from '../src/types/contracts'

vi.mock('../src/services/contractsApi', () => ({
  listContracts: vi.fn(),
  renewContract: vi.fn(),
}))

import { listContracts } from '../src/services/contractsApi'

const mockListContracts = listContracts as ReturnType<typeof vi.fn>

function makeItem(overrides: Partial<ContractListResponse['items'][0]> = {}) {
  return {
    id: 1,
    ref_id: 'CON-0001',
    value: '5000.00',
    start_date: '2026-01-01',
    end_date: '2026-12-31',
    status: 'Draft' as const,
    is_renewal_due: false,
    is_archived: false,
    owner_id: 1,
    account_id: 1,
    deal_id: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ContractList', () => {
  it('renders contract rows from the API', async () => {
    mockListContracts.mockResolvedValue({
      total: 1,
      page: 1,
      limit: 20,
      items: [makeItem()],
    } satisfies ContractListResponse)

    render(
      <Wrapper>
        <ContractList />
      </Wrapper>,
    )

    await waitFor(() => expect(screen.getByText('CON-0001')).toBeInTheDocument())
    expect(screen.getByText('Draft')).toBeInTheDocument()
  })

  it('shows renewal due badge when is_renewal_due is true', async () => {
    mockListContracts.mockResolvedValue({
      total: 1,
      page: 1,
      limit: 20,
      items: [makeItem({ is_renewal_due: true, status: 'Active' })],
    } satisfies ContractListResponse)

    render(
      <Wrapper>
        <ContractList />
      </Wrapper>,
    )

    await waitFor(() =>
      expect(screen.getByLabelText('Renewal due')).toBeInTheDocument(),
    )
  })
})
