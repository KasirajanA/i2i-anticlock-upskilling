import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

const mockUseUserList = vi.fn()
const mockUseCreateUser = vi.fn()
const mockUseUpdateUserRole = vi.fn()
const mockUseDeactivateUser = vi.fn()

vi.mock('../../hooks/useUsers', () => ({
  useUserList: () => mockUseUserList(),
  useCreateUser: () => mockUseCreateUser(),
  useUpdateUserRole: () => mockUseUpdateUserRole(),
  useDeactivateUser: () => mockUseDeactivateUser(),
}))

import UserListPage from '../../pages/UserListPage'

const mockUsers = [
  { id: 1, name: 'Alice', email: 'alice@test.com', role: 'Admin', is_active: true, display_name: null, avatar_url: null, timezone: 'UTC', created_at: '2026-01-01T00:00:00' },
  { id: 2, name: 'Bob', email: 'bob@test.com', role: 'Sales Rep', is_active: true, display_name: 'Bobby', avatar_url: null, timezone: 'UTC', created_at: '2026-01-01T00:00:00' },
]

describe('UserListPage', () => {
  beforeEach(() => {
    mockUseCreateUser.mockReturnValue({ mutate: vi.fn(), isPending: false })
    mockUseUpdateUserRole.mockReturnValue({ mutate: vi.fn() })
    mockUseDeactivateUser.mockReturnValue({ mutate: vi.fn() })
  })

  it('renders user list', () => {
    mockUseUserList.mockReturnValue({ data: { items: mockUsers, total: 2 }, isLoading: false })
    render(<MemoryRouter><UserListPage /></MemoryRouter>)
    expect(screen.getByText('alice@test.com')).toBeTruthy()
    expect(screen.getByText('Bobby')).toBeTruthy()
  })

  it('shows loading spinner when loading', () => {
    mockUseUserList.mockReturnValue({ data: undefined, isLoading: true })
    render(<MemoryRouter><UserListPage /></MemoryRouter>)
    expect(screen.queryByText('alice@test.com')).toBeNull()
  })

  it('shows Add User button', () => {
    mockUseUserList.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false })
    render(<MemoryRouter><UserListPage /></MemoryRouter>)
    expect(screen.getByText('Add User')).toBeTruthy()
  })
})
