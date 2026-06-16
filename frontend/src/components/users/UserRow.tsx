import TableCell from '@mui/material/TableCell'
import TableRow from '@mui/material/TableRow'
import IconButton from '@mui/material/IconButton'
import Tooltip from '@mui/material/Tooltip'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import PersonOffIcon from '@mui/icons-material/PersonOff'
import LockOpenIcon from '@mui/icons-material/LockOpen'
import type { UserProfile } from '../../types/user'
import type { Role } from '../../types/auth'
import RoleBadge from './RoleBadge'

const ROLES: Role[] = ['Admin', 'Manager', 'Sales Rep', 'Support Agent']

interface Props {
  user: UserProfile
  onRoleChange: (userId: number, role: Role) => void
  onDeactivate: (userId: number) => void
  onUnlock: (userId: number) => void
}

export default function UserRow({ user, onRoleChange, onDeactivate, onUnlock }: Props) {
  return (
    <TableRow>
      <TableCell>{user.display_name ?? user.name}</TableCell>
      <TableCell>{user.email}</TableCell>
      <TableCell>
        <Select
          size="small"
          value={user.role}
          onChange={(e) => onRoleChange(user.id, e.target.value as Role)}
          disabled={!user.is_active}
        >
          {ROLES.map((r) => (
            <MenuItem key={r} value={r}>
              <RoleBadge role={r} />
            </MenuItem>
          ))}
        </Select>
      </TableCell>
      <TableCell>{user.is_active ? 'Active' : 'Inactive'}</TableCell>
      <TableCell>
        {user.is_active && (
          <Tooltip title="Deactivate">
            <IconButton size="small" onClick={() => onDeactivate(user.id)}>
              <PersonOffIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
        {user.locked && (
          <Tooltip title="Unlock">
            <IconButton size="small" onClick={() => onUnlock(user.id)}>
              <LockOpenIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </TableCell>
    </TableRow>
  )
}
