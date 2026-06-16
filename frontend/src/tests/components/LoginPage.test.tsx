import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext } from '../../context/AuthContext'
import LoginForm from '../../components/auth/LoginForm'
import type { AuthContextValue } from '../../types/auth'

const mockLogin = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderWithAuth(loginFn = mockLogin) {
  const ctx: AuthContextValue = {
    user: null,
    isLoading: false,
    login: loginFn,
    logout: vi.fn(),
  }
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={ctx}>
        <LoginForm />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('LoginForm', () => {
  it('shows password inline error when password is too short', async () => {
    renderWithAuth()
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'short' } })
    fireEvent.submit(screen.getByRole('button', { name: /Sign In/i }).closest('form')!)
    expect(screen.getByText('Password must be at least 8 characters.')).toBeTruthy()
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('shows email error when email is invalid', async () => {
    renderWithAuth()
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'notanemail' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'validpass1' } })
    fireEvent.submit(screen.getByRole('button', { name: /Sign In/i }).closest('form')!)
    expect(screen.getByText('Enter a valid email address.')).toBeTruthy()
  })

  it('shows generic error message on 401', async () => {
    const failLogin = vi.fn().mockRejectedValueOnce(new Error('Invalid username or password.'))
    renderWithAuth(failLogin)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'validpass1' } })
    fireEvent.submit(screen.getByRole('button', { name: /Sign In/i }).closest('form')!)
    await waitFor(() => expect(screen.getByText('Invalid username or password.')).toBeTruthy())
  })

  it('navigates to dashboard on successful login', async () => {
    const successLogin = vi.fn().mockResolvedValueOnce(undefined)
    renderWithAuth(successLogin)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'validpass1' } })
    fireEvent.submit(screen.getByRole('button', { name: /Sign In/i }).closest('form')!)
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/dashboard'))
  })
})
