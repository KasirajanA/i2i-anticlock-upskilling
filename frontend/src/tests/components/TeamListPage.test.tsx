import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

const mockUseTeamList = vi.fn()
const mockUseCreateTeam = vi.fn()
const mockUseUserList = vi.fn()

vi.mock('../../hooks/useTeams', () => ({
  useTeamList: () => mockUseTeamList(),
  useCreateTeam: () => mockUseCreateTeam(),
}))

vi.mock('../../hooks/useUsers', () => ({
  useUserList: () => mockUseUserList(),
  useCreateUser: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateUserRole: () => ({ mutate: vi.fn() }),
  useDeactivateUser: () => ({ mutate: vi.fn() }),
}))

import TeamListPage from '../../pages/TeamListPage'

const mockTeams = [
  { id: 1, name: 'EMEA Sales', lead_user_id: 2, created_by_id: 1, created_at: '2026-01-01T00:00:00', member_count: 3 },
]

describe('TeamListPage', () => {
  beforeEach(() => {
    mockUseCreateTeam.mockReturnValue({ mutateAsync: vi.fn(), isPending: false })
    mockUseUserList.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false })
  })

  it('renders team cards', () => {
    mockUseTeamList.mockReturnValue({ data: { items: mockTeams, total: 1 }, isLoading: false })
    render(<MemoryRouter><TeamListPage /></MemoryRouter>)
    expect(screen.getByText('EMEA Sales')).toBeTruthy()
    expect(screen.getByText('3 members')).toBeTruthy()
  })

  it('shows empty state when no teams', () => {
    mockUseTeamList.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false })
    render(<MemoryRouter><TeamListPage /></MemoryRouter>)
    expect(screen.getByText('No teams yet.')).toBeTruthy()
  })

  it('shows Create Team button', () => {
    mockUseTeamList.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false })
    render(<MemoryRouter><TeamListPage /></MemoryRouter>)
    expect(screen.getByText('Create Team')).toBeTruthy()
  })
})
