import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TicketDetail from '../../components/support/TicketDetail'

const mockTicket = {
  id: 1,
  ref: 'I2I-CRM-0001',
  subject: 'Login issue',
  description: 'Cannot log in',
  status: 'open' as const,
  priority: 'high' as const,
  contact_id: 1,
  contact_name_snapshot: 'Alice',
  account_id: null,
  assignee_id: null,
  created_by_id: 1,
  sla: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

vi.mock('../../hooks/useTickets', () => ({
  useTicket: () => ({
    data: mockTicket,
    isLoading: false,
    isError: false,
  }),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn().mockReturnValue({ data: { items: [] } }),
  }
})

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient()
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('TicketDetail', () => {
  it('renders ticket subject', () => {
    render(<TicketDetail ticketId={1} isAgent={false} />, { wrapper })
    expect(screen.getByText(/Login issue/)).toBeTruthy()
  })

  it('renders description', () => {
    render(<TicketDetail ticketId={1} isAgent={false} />, { wrapper })
    expect(screen.getByText('Cannot log in')).toBeTruthy()
  })

  it('renders status chip', () => {
    render(<TicketDetail ticketId={1} isAgent={false} />, { wrapper })
    expect(screen.getByText('Open')).toBeTruthy()
  })
})
