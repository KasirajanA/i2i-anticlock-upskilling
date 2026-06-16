import CircularProgress from '@mui/material/CircularProgress'
import Box from '@mui/material/Box'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

interface Props {
  children: React.ReactNode
}

export default function SessionGuard({ children }: Props) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
