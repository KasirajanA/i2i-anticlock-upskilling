import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ReplyForm from '../../components/support/ReplyForm'

const mockMutate = vi.fn()

vi.mock('../../hooks/useTicketMutations', () => ({
  useAddReply: () => ({ mutate: mockMutate, isPending: false }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient()
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('ReplyForm', () => {
  it('renders text field and send button', () => {
    render(<ReplyForm ticketId={1} isAgent={false} />, { wrapper })
    expect(screen.getByLabelText('Reply')).toBeTruthy()
    expect(screen.getByText('Send')).toBeTruthy()
  })

  it('shows internal note toggle for agents', () => {
    render(<ReplyForm ticketId={1} isAgent />, { wrapper })
    expect(screen.getByText('Internal note')).toBeTruthy()
  })

  it('does not show internal note toggle for non-agents', () => {
    render(<ReplyForm ticketId={1} isAgent={false} />, { wrapper })
    expect(screen.queryByText('Internal note')).toBeNull()
  })

  it('calls mutate on submit with body text', () => {
    render(<ReplyForm ticketId={1} isAgent={false} />, { wrapper })
    fireEvent.change(screen.getByLabelText('Reply'), { target: { value: 'Hello' } })
    fireEvent.submit(screen.getByRole('form', { name: '' }) ?? screen.getByText('Send').closest('form')!)
    expect(mockMutate).toHaveBeenCalled()
  })
})
