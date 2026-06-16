import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TicketQueue from '../../components/support/TicketQueue'

vi.mock('../../hooks/useTickets', () => ({
  useTickets: () => ({
    data: {
      pages: [
        {
          items: [
            {
              id: 1,
              ref: 'I2I-CRM-0001',
              subject: 'Test ticket',
              status: 'open',
              priority: 'medium',
              contact_name: 'John Doe',
              assignee_id: null,
              sla: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
          next_cursor: null,
        },
      ],
    },
    fetchNextPage: vi.fn(),
    hasNextPage: false,
    isFetchingNextPage: false,
    isLoading: false,
    isError: false,
  }),
}))

vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient()
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('TicketQueue', () => {
  it('renders ticket rows', () => {
    render(<TicketQueue />, { wrapper })
    expect(screen.getByText('I2I-CRM-0001')).toBeTruthy()
    expect(screen.getByText('Test ticket')).toBeTruthy()
  })

  it('shows empty state when no tickets', () => {
    vi.mocked(await import('../../hooks/useTickets')).useTickets = () => ({
      data: { pages: [{ items: [], next_cursor: null }] },
      fetchNextPage: vi.fn(),
      hasNextPage: false,
      isFetchingNextPage: false,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof import('../../hooks/useTickets').useTickets>)

    render(<TicketQueue />, { wrapper })
    expect(screen.getByText('No tickets found.')).toBeTruthy()
  })
})
