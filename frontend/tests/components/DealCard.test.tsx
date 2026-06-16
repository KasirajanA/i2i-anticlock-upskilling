import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import DealCard from '../../src/components/pipeline/DealCard'
import type { DealSummary } from '../../src/types/deal'

function makeDeal(overrides: Partial<DealSummary> = {}): DealSummary {
  return {
    id: 1,
    ref_id: 'DEAL-0001',
    title: 'Acme Expansion',
    value: '15000.00',
    stage: 'Lead In',
    expected_close_date: '2026-09-30',
    is_overdue: false,
    owner: { id: 1, name: 'Alice', email: 'alice@example.com' },
    account: { id: 1, name: 'Acme Corp' },
    ...overrides,
  }
}

describe('DealCard', () => {
  it('shows title, account name, value, and close date', () => {
    render(<DealCard deal={makeDeal()} onSelect={() => {}} />)
    expect(screen.getByText('Acme Expansion')).toBeInTheDocument()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText(/15,000/)).toBeInTheDocument()
    expect(screen.getByText(/2026-09-30/)).toBeInTheDocument()
  })

  it('shows overdue badge when is_overdue is true', () => {
    render(<DealCard deal={makeDeal({ is_overdue: true })} onSelect={() => {}} />)
    expect(screen.getByLabelText('Overdue')).toBeInTheDocument()
  })

  it('does not show overdue badge when is_overdue is false', () => {
    render(<DealCard deal={makeDeal({ is_overdue: false })} onSelect={() => {}} />)
    expect(screen.queryByLabelText('Overdue')).not.toBeInTheDocument()
  })
})
