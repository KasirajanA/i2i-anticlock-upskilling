import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SupportReportPage from '../../pages/SupportReportPage'

vi.mock('../../hooks/useAnalytics', () => ({
  useSupportReport: () => ({
    data: {
      status_breakdown: [{ status: 'open', count: 5 }],
      priority_breakdown: [{ priority: 'high', count: 2 }],
      avg_resolution_hours: 4.5,
      sla_breach_rate: 0.1,
      per_agent: [{ assignee_id: 1, assignee_name: 'Bob', count: 3 }],
      filters_applied: {},
      cached_until: new Date(Date.now() + 60_000).toISOString(),
    },
    isLoading: false,
    isError: false,
  }),
}))

vi.mock('../../services/analyticsApi', () => ({
  exportSupportReport: vi.fn(),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

describe('SupportReportPage', () => {
  it('renders status breakdown table', () => {
    render(<SupportReportPage />, { wrapper })
    expect(screen.getByText('By Status')).toBeTruthy()
    expect(screen.getByText('open')).toBeTruthy()
  })

  it('renders SLA breach rate', () => {
    render(<SupportReportPage />, { wrapper })
    expect(screen.getByText(/SLA Breach Rate:/)).toBeTruthy()
    expect(screen.getByText(/10.0%/)).toBeTruthy()
  })

  it('shows CacheTimer for 1-minute refresh', () => {
    render(<SupportReportPage />, { wrapper })
    expect(screen.getByText(/Refreshing in/)).toBeTruthy()
  })
})
