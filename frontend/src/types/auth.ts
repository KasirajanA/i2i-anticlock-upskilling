export type Role = 'Admin' | 'Manager' | 'Sales Rep' | 'Support Agent'

export interface User {
  id: number
  name: string
  email: string
  role: Role
  is_active: boolean
}

export interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}
