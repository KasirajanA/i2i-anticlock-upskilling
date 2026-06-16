import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import ContractForm from '../src/components/contracts/ContractForm'

describe('ContractForm — create mode', () => {
  it('shows inline error for missing required fields', async () => {
    const onSubmit = vi.fn()
    render(<ContractForm mode="create" onSubmit={onSubmit} />)

    fireEvent.submit(screen.getByRole('button', { name: /Create Contract/i }))

    await waitFor(() => {
      expect(screen.getByText('Value must be greater than 0')).toBeInTheDocument()
      expect(screen.getByText('Account is required')).toBeInTheDocument()
      expect(screen.getByText('Start date is required')).toBeInTheDocument()
      expect(screen.getByText('End date is required')).toBeInTheDocument()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('shows cross-field error when end_date is before start_date', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ContractForm mode="create" onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText('Contract value'), '1000')
    await user.type(screen.getByLabelText('Account ID'), '1')

    fireEvent.change(screen.getByLabelText('Start date'), {
      target: { value: '2026-12-31' },
    })
    fireEvent.change(screen.getByLabelText('End date'), {
      target: { value: '2026-01-01' },
    })

    fireEvent.submit(screen.getByRole('button', { name: /Create Contract/i }))

    await waitFor(() => {
      expect(
        screen.getByText('End date must be on or after start date'),
      ).toBeInTheDocument()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit with valid data', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ContractForm mode="create" onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText('Contract value'), '5000')
    await user.type(screen.getByLabelText('Account ID'), '1')
    fireEvent.change(screen.getByLabelText('Start date'), {
      target: { value: '2026-01-01' },
    })
    fireEvent.change(screen.getByLabelText('End date'), {
      target: { value: '2026-12-31' },
    })

    await user.click(screen.getByRole('button', { name: /Create Contract/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          value: 5000,
          start_date: '2026-01-01',
          end_date: '2026-12-31',
          account_id: 1,
        }),
      )
    })
  })
})
