import { Navigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import type { Role } from '../../types/auth'

interface Props {
  allowedRoles: Role[]
  children: React.ReactNode
}

export default function RequireRole({ allowedRoles, children }: Props) {
  const { user } = useAuth()

  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to="/access-denied" replace />
  }

  return <>{children}</>
}
