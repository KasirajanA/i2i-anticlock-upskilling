import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Stack from '@mui/material/Stack'
import { Link } from 'react-router-dom'
import TicketQueue from '../components/support/TicketQueue'
import type { TicketFilters, TicketStatus, TicketPriority } from '../types/support'

export default function SupportQueuePage() {
  const [queue, setQueue] = useState<'mine' | 'unassigned' | 'all'>('all')
  const [status, setStatus] = useState<TicketStatus | ''>('')
  const [priority, setPriority] = useState<TicketPriority | ''>('')

  const filters: TicketFilters = {
    queue,
    ...(status ? { status } : {}),
    ...(priority ? { priority } : {}),
  }

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Support Tickets</Typography>
        <Button variant="contained" component={Link} to="/support/new">
          New Ticket
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} mb={2}>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Queue</InputLabel>
          <Select
            label="Queue"
            value={queue}
            onChange={(e) => setQueue(e.target.value as typeof queue)}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="mine">Mine</MenuItem>
            <MenuItem value="unassigned">Unassigned</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Status</InputLabel>
          <Select
            label="Status"
            value={status}
            onChange={(e) => setStatus(e.target.value as typeof status)}
          >
            <MenuItem value="">Any</MenuItem>
            <MenuItem value="open">Open</MenuItem>
            <MenuItem value="in_progress">In Progress</MenuItem>
            <MenuItem value="resolved">Resolved</MenuItem>
            <MenuItem value="closed">Closed</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Priority</InputLabel>
          <Select
            label="Priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as typeof priority)}
          >
            <MenuItem value="">Any</MenuItem>
            <MenuItem value="low">Low</MenuItem>
            <MenuItem value="medium">Medium</MenuItem>
            <MenuItem value="high">High</MenuItem>
            <MenuItem value="critical">Critical</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      <TicketQueue filters={filters} />
    </Box>
  )
}
