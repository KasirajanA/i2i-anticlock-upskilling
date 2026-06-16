import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import DealForm from '../../src/components/pipeline/DealForm'

vi.mock('../../src/services/dealService', () => ({
  createDeal: vi.fn(),
  listDeals: vi.fn(),
  getDeal: vi.fn(),
  updateDeal: vi.fn(),
}))

import { createDeal } from '../../src/services/dealService'
const mockCreate = createDeal as ReturnType<typeof vi.fn>

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('DealForm', () => {
  it('shows validation errors on empty submit', async () => {
    const user = userEvent.setup()
    render(
      <Wrapper>
        <DealForm open onClose={() => {}} />
      </Wrapper>,
    )
    await user.click(screen.getByRole('button', { name: /create/i }))
    await waitFor(() => {
      expect(screen.getAllByText(/required/i).length).toBeGreaterThan(0)
    })
    expect(mockCreate).not.toHaveBeenCalled()
  })

  it('calls createDeal with correct payload on valid submit', async () => {
    mockCreate.mockResolvedValue({
      id: 1,
      ref_id: 'DEAL-0001',
      title: 'Test',
      value: '5000.00',
      stage: 'Lead In',
      expected_close_date: '2026-12-31',
      is_overdue: false,
      is_archived: false,
      loss_reason: null,
      owner: { id: 1, name: 'Alice', email: 'a@b.com' },
      account: { id: 1, name: 'Acme' },
      contact: null,
      created_at: '',
      updated_at: '',
    })

    const user = userEvent.setup()
    const onClose = vi.fn()
    render(
      <Wrapper>
        <DealForm open onClose={onClose} />
      </Wrapper>,
    )

    await user.type(screen.getByLabelText(/title/i), 'Test')
    await user.type(screen.getByLabelText(/value/i), '5000')
    await user.type(screen.getByLabelText(/close date/i), '2026-12-31')
    await user.type(screen.getByLabelText(/account id/i), '1')
    await user.type(screen.getByLabelText(/owner id/i), '1')
    await user.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() => expect(mockCreate).toHaveBeenCalled())
    const payload = mockCreate.mock.calls[0][0]
    expect(payload.title).toBe('Test')
    expect(payload.account_id).toBe(1)
  })
})
