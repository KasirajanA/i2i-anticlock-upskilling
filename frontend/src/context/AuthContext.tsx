import { createContext, useCallback, useEffect, useState } from 'react'
import type { AuthContextValue, User } from '../types/auth'

export const AuthContext = createContext<AuthContextValue | null>(null)

interface Props {
  children: React.ReactNode
}

export function AuthProvider({ children }: Props) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetch('/api/v1/auth/me', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setUser(data ?? null))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const resp = await fetch('/api/v1/auth/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(body.detail ?? 'Login failed')
    }
    const body = await resp.json()
    setUser(body.user)
  }, [])

  const logout = useCallback(async () => {
    await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' })
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
