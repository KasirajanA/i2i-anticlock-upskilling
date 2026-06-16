import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext } from '../../context/AuthContext'
import RequireRole from '../../components/auth/RequireRole'
import type { AuthContextValue, User } from '../../types/auth'

const makeCtx = (role: User['role'] | null): AuthContextValue => ({
  user: role ? { id: 1, name: 'Test', email: 't@t.com', role, is_active: true } : null,
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
})

describe('RequireRole', () => {
  it('renders children when user has allowed role', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={makeCtx('Admin')}>
          <RequireRole allowedRoles={['Admin']}>
            <div>Admin Content</div>
          </RequireRole>
        </AuthContext.Provider>
      </MemoryRouter>
    )
    expect(screen.getByText('Admin Content')).toBeTruthy()
  })

  it('redirects when user role is not allowed', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={makeCtx('Sales Rep')}>
          <RequireRole allowedRoles={['Admin']}>
            <div>Admin Content</div>
          </RequireRole>
        </AuthContext.Provider>
      </MemoryRouter>
    )
    expect(screen.queryByText('Admin Content')).toBeNull()
  })

  it('redirects when user is null', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={makeCtx(null)}>
          <RequireRole allowedRoles={['Admin']}>
            <div>Admin Content</div>
          </RequireRole>
        </AuthContext.Provider>
      </MemoryRouter>
    )
    expect(screen.queryByText('Admin Content')).toBeNull()
  })
})
