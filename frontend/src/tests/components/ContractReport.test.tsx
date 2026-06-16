import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ContractReportPage from '../../pages/ContractReportPage'

const mockUseContractReport = vi.fn(() => ({
  data: {
    status_breakdown: [],
    upcoming_renewals: [
      {
        contract_id: 1,
        ref_id: 'CTR-001',
        account_name: 'Acme',
        value: '5000',
        expiry_date: '2026-07-01',
        days_remaining: 15,
      },
    ],
    value_by_account: [],
    filters_applied: {},
    cached_until: null,
  },
  isLoading: false,
  isError: false,
}))

vi.mock('../../hooks/useAnalytics', () => ({
  useContractReport: (...args: unknown[]) => mockUseContractReport(...args),
}))

vi.mock('../../services/analyticsApi', () => ({
  exportContractReport: vi.fn(),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

describe('ContractReportPage', () => {
  it('renders upcoming renewals table', () => {
    render(<ContractReportPage />, { wrapper })
    expect(screen.getByText('Upcoming Renewals')).toBeTruthy()
    expect(screen.getByText('CTR-001')).toBeTruthy()
    expect(screen.getByText('15')).toBeTruthy()
  })

  it('renders renewal window selector', () => {
    render(<ContractReportPage />, { wrapper })
    expect(screen.getByLabelText('Renewal Window')).toBeTruthy()
  })
})
