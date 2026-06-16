import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SalesReportPage from '../../pages/SalesReportPage'

vi.mock('../../hooks/useAnalytics', () => ({
  useSalesReport: () => ({
    data: {
      stage_breakdown: [
        { stage: 'qualified', count: 2, total_value: '5000' },
        { stage: 'closed_won', count: 1, total_value: '3000' },
      ],
      won_count: 1,
      lost_count: 0,
      avg_deal_value: '3000',
      top_reps: [{ owner_id: 1, owner_name: 'Alice', revenue: '3000' }],
      filters_applied: {},
      cached_until: null,
    },
    isLoading: false,
    isError: false,
  }),
}))

vi.mock('../../services/analyticsApi', () => ({
  exportSalesReport: vi.fn(),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

describe('SalesReportPage', () => {
  it('renders stage breakdown table', () => {
    render(<SalesReportPage />, { wrapper })
    expect(screen.getByText('Stage Breakdown')).toBeTruthy()
    expect(screen.getByText('qualified')).toBeTruthy()
  })

  it('renders top reps table', () => {
    render(<SalesReportPage />, { wrapper })
    expect(screen.getByText('Alice')).toBeTruthy()
  })

  it('shows won and lost counts', () => {
    render(<SalesReportPage />, { wrapper })
    expect(screen.getByText(/Won:/)).toBeTruthy()
  })
})
