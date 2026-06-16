import { useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import MenuItem from '@mui/material/MenuItem'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import PersonAddIcon from '@mui/icons-material/PersonAdd'
import UserRow from '../components/users/UserRow'
import {
  useCreateUser,
  useDeactivateUser,
  useUpdateUserRole,
  useUserList,
} from '../hooks/useUsers'
import type { Role } from '../types/auth'

const ROLES: Role[] = ['Admin', 'Manager', 'Sales Rep', 'Support Agent']

export default function UserListPage() {
  const { data, isLoading } = useUserList()
  const createUser = useCreateUser()
  const updateRole = useUpdateUserRole()
  const deactivate = useDeactivateUser()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', role: 'Sales Rep' as Role, password: '' })

  if (isLoading) return <CircularProgress sx={{ m: 4 }} />

  const users = data?.items ?? []

  async function handleCreate() {
    await createUser.mutateAsync(form)
    setOpen(false)
    setForm({ name: '', email: '', role: 'Sales Rep', password: '' })
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Users</Typography>
        <Button startIcon={<PersonAddIcon />} variant="contained" onClick={() => setOpen(true)}>
          Add User
        </Button>
      </Box>

      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Email</TableCell>
            <TableCell>Role</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {users.map((u) => (
            <UserRow
              key={u.id}
              user={u}
              onRoleChange={(id, role) => updateRole.mutate({ userId: id, role })}
              onDeactivate={(id) => deactivate.mutate(id)}
              onUnlock={() => {}}
            />
          ))}
        </TableBody>
      </Table>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add User</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
          <TextField
            label="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            fullWidth
          />
          <TextField
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            fullWidth
          />
          <TextField
            select
            label="Role"
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
            fullWidth
          >
            {ROLES.map((r) => <MenuItem key={r} value={r}>{r}</MenuItem>)}
          </TextField>
          <TextField
            label="Password"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            fullWidth
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={createUser.isPending}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
