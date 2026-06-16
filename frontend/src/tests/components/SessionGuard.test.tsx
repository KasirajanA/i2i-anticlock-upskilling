import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext } from '../../context/AuthContext'
import SessionGuard from '../../components/auth/SessionGuard'
import type { AuthContextValue, User } from '../../types/auth'

const mockUser: User = { id: 1, name: 'Alice', email: 'alice@example.com', role: 'Admin', is_active: true }

function renderGuard(user: User | null, isLoading = false) {
  const ctx: AuthContextValue = {
    user,
    isLoading,
    login: vi.fn(),
    logout: vi.fn(),
  }
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={ctx}>
        <SessionGuard>
          <div>Protected Content</div>
        </SessionGuard>
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('SessionGuard', () => {
  it('renders children when user is logged in', () => {
    renderGuard(mockUser)
    expect(screen.getByText('Protected Content')).toBeTruthy()
  })

  it('shows CircularProgress while loading', () => {
    renderGuard(null, true)
    expect(screen.queryByText('Protected Content')).toBeNull()
  })

  it('redirects to /login when user is null', () => {
    const { container } = renderGuard(null)
    expect(screen.queryByText('Protected Content')).toBeNull()
  })
})
