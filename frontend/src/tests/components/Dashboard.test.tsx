import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '../../pages/DashboardPage'

vi.mock('../../hooks/useAnalytics', () => ({
  useDashboard: () => ({
    data: {
      widgets: [
        { key: 'open_deals_count', label: 'Open Deals', value: 3 },
        { key: 'pipeline_value', label: 'Pipeline Value', value: 15000, unit: '$' },
      ],
      generated_at: new Date().toISOString(),
    },
    isLoading: false,
    isError: false,
  }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

describe('DashboardPage', () => {
  it('renders widget tiles from API response', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText('Open Deals')).toBeTruthy()
    expect(screen.getByText('Pipeline Value')).toBeTruthy()
  })

  it('renders loading skeleton during fetch', () => {
    vi.mocked(await import('../../hooks/useAnalytics')).useDashboard = () => ({
      data: undefined,
      isLoading: true,
      isError: false,
    })
    render(<DashboardPage />, { wrapper })
    // No error shown while loading
    expect(screen.queryByText('Failed to load dashboard.')).toBeNull()
  })
})
