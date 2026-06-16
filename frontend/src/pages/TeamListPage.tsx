import { useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import Grid from '@mui/material/Grid'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import GroupAddIcon from '@mui/icons-material/GroupAdd'
import TeamCard from '../components/users/TeamCard'
import MemberPicker from '../components/users/MemberPicker'
import { useCreateTeam, useTeamList } from '../hooks/useTeams'
import type { UserProfile } from '../types/user'

export default function TeamListPage() {
  const { data, isLoading } = useTeamList()
  const createTeam = useCreateTeam()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [members, setMembers] = useState<UserProfile[]>([])

  if (isLoading) return <CircularProgress sx={{ m: 4 }} />

  const teams = data?.items ?? []

  async function handleCreate() {
    await createTeam.mutateAsync({
      name,
      member_ids: members.map((m) => m.id),
    })
    setOpen(false)
    setName('')
    setMembers([])
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Teams</Typography>
        <Button startIcon={<GroupAddIcon />} variant="contained" onClick={() => setOpen(true)}>
          Create Team
        </Button>
      </Box>

      {teams.length === 0 ? (
        <Typography color="text.secondary">No teams yet.</Typography>
      ) : (
        <Grid container spacing={2}>
          {teams.map((t) => (
            <Grid item xs={12} sm={6} md={4} key={t.id}>
              <TeamCard team={t} />
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Team</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
          <TextField
            label="Team Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
          />
          <MemberPicker value={members} onChange={setMembers} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={createTeam.isPending}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
