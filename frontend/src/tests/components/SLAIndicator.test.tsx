import { render, screen } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import SLAIndicator from '../../components/support/SLAIndicator'
import type { SLASummary } from '../../types/support'

function makeSLA(overrides: Partial<SLASummary> = {}): SLASummary {
  const now = new Date()
  return {
    first_response_due: new Date(now.getTime() + 2 * 3600 * 1000).toISOString(),
    resolution_due: new Date(now.getTime() + 8 * 3600 * 1000).toISOString(),
    first_response_breached: false,
    resolution_breached: false,
    warning: false,
    ...overrides,
  }
}

describe('SLAIndicator', () => {
  it('renders nothing when sla is null', () => {
    const { container } = render(<SLAIndicator sla={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('shows Breached when first_response_breached is true', () => {
    render(<SLAIndicator sla={makeSLA({ first_response_breached: true })} />)
    expect(screen.getByLabelText('SLA Breached')).toBeTruthy()
  })

  it('shows warning when due in under an hour', () => {
    const sla = makeSLA({
      first_response_due: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    })
    render(<SLAIndicator sla={sla} />)
    expect(screen.getByLabelText('SLA Warning')).toBeTruthy()
  })

  it('shows OK chip when plenty of time remains', () => {
    render(<SLAIndicator sla={makeSLA()} />)
    expect(screen.getByLabelText('SLA OK')).toBeTruthy()
  })
})
