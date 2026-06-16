import Chip from '@mui/material/Chip'
import type { Role } from '../../types/auth'

const COLOR_MAP: Record<Role, 'error' | 'warning' | 'info' | 'default'> = {
  Admin: 'error',
  Manager: 'warning',
  'Sales Rep': 'info',
  'Support Agent': 'default',
}

interface Props {
  role: Role
}

export default function RoleBadge({ role }: Props) {
  return <Chip label={role} color={COLOR_MAP[role]} size="small" />
}
