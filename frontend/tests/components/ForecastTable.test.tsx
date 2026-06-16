import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ForecastTable from '../../src/components/pipeline/ForecastTable'
import type { ForecastResponse } from '../../src/types/deal'

const mockData: ForecastResponse = {
  period_start: '2026-07-01',
  period_end: '2026-09-30',
  open_pipeline: [
    {
      stage: 'Lead In',
      deal_count: 1,
      total_value: '10000.00',
      probability: '0.10',
      weighted_value: '1000.00',
    },
    {
      stage: 'Qualified',
      deal_count: 1,
      total_value: '20000.00',
      probability: '0.25',
      weighted_value: '5000.00',
    },
    {
      stage: 'Proposal',
      deal_count: 1,
      total_value: '30000.00',
      probability: '0.50',
      weighted_value: '15000.00',
    },
    {
      stage: 'Negotiation',
      deal_count: 1,
      total_value: '40000.00',
      probability: '0.75',
      weighted_value: '30000.00',
    },
  ],
  closed_won: {
    deal_count: 2,
    total_value: '25000.00',
  },
  total_weighted_forecast: '51000.00',
}

describe('ForecastTable', () => {
  it('renders stage rows from forecast data', () => {
    render(<ForecastTable data={mockData} />)
    expect(screen.getByText('Lead In')).toBeInTheDocument()
    expect(screen.getByText('Qualified')).toBeInTheDocument()
    expect(screen.getByText('Proposal')).toBeInTheDocument()
    expect(screen.getByText('Negotiation')).toBeInTheDocument()
  })

  it('shows weighted values formatted to 2 decimal places', () => {
    render(<ForecastTable data={mockData} />)
    expect(screen.getByText('$1000.00')).toBeInTheDocument()
    expect(screen.getByText('$5000.00')).toBeInTheDocument()
    expect(screen.getByText('$15000.00')).toBeInTheDocument()
    expect(screen.getByText('$30000.00')).toBeInTheDocument()
  })

  it('shows Closed Won as a separate row', () => {
    render(<ForecastTable data={mockData} />)
    expect(screen.getByText('Closed Won')).toBeInTheDocument()
  })

  it('shows total weighted forecast', () => {
    render(<ForecastTable data={mockData} />)
    expect(screen.getByText('$51000.00')).toBeInTheDocument()
  })
})
