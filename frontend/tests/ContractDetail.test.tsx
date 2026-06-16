import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import ContractDetail from '../src/components/contracts/ContractDetail'
import type { Contract, ActivityLogResponse } from '../src/types/contracts'

vi.mock('../src/services/contractsApi', () => ({
  getActivityLog: vi.fn(),
  deleteAttachment: vi.fn(),
  uploadAttachment: vi.fn(),
  transitionContract: vi.fn(),
}))

import { getActivityLog } from '../src/services/contractsApi'

const mockGetActivityLog = getActivityLog as ReturnType<typeof vi.fn>

const mockContract: Contract = {
  id: 1,
  ref_id: 'CON-0001',
  value: '12500.00',
  start_date: '2026-01-01',
  end_date: '2026-12-31',
  status: 'Active',
  description: 'Test contract description',
  is_renewal_due: false,
  is_archived: false,
  owner_id: 1,
  account_id: 3,
  deal_id: null,
  created_at: '2026-01-01T09:00:00Z',
  updated_at: '2026-06-01T12:00:00Z',
  attachment: {
    id: 1,
    contract_id: 1,
    filename: 'agreement.pdf',
    mime_type: 'application/pdf',
    size_bytes: 102400,
    created_at: '2026-01-10T11:00:00Z',
  },
}

const mockLogs: ActivityLogResponse = {
  ref_id: 'CON-0001',
  logs: [
    {
      id: 2,
      action_type: 'status_transition',
      actor_id: 1,
      actor_name: 'Jane Smith',
      note: null,
      created_at: '2026-03-15T14:22:00Z',
    },
    {
      id: 1,
      action_type: 'attachment_added',
      actor_id: 1,
      actor_name: 'Jane Smith',
      note: 'Initial upload',
      created_at: '2026-01-10T11:00:00Z',
    },
  ],
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ContractDetail', () => {
  it('renders all contract fields', () => {
    mockGetActivityLog.mockResolvedValue(mockLogs)
    render(
      <Wrapper>
        <ContractDetail contract={mockContract} userId={1} userRole="Sales Rep" />
      </Wrapper>,
    )

    expect(screen.getByText('CON-0001')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Test contract description')).toBeInTheDocument()
    expect(screen.getByText('2026-01-01 — 2026-12-31')).toBeInTheDocument()
  })

  it('shows ContractAttachmentPanel with filename', () => {
    mockGetActivityLog.mockResolvedValue(mockLogs)
    render(
      <Wrapper>
        <ContractDetail contract={mockContract} userId={1} userRole="Sales Rep" />
      </Wrapper>,
    )

    expect(screen.getByText('agreement.pdf')).toBeInTheDocument()
  })

  it('shows ContractActivityLog timeline entries', async () => {
    mockGetActivityLog.mockResolvedValue(mockLogs)
    render(
      <Wrapper>
        <ContractDetail contract={mockContract} userId={1} userRole="Sales Rep" />
      </Wrapper>,
    )

    await waitFor(() => {
      expect(screen.getByText('Status Change')).toBeInTheDocument()
      expect(screen.getByText('Attachment Added')).toBeInTheDocument()
    })
  })
})
