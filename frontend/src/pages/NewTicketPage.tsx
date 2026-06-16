import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Stack from '@mui/material/Stack'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import { useNavigate, Link } from 'react-router-dom'
import { useCreateTicket } from '../hooks/useTicketMutations'

export default function NewTicketPage() {
  const navigate = useNavigate()
  const { mutate: createTicket, isPending, error } = useCreateTicket()

  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [contactId, setContactId] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!subject.trim() || !contactId) return
    createTicket(
      {
        subject: subject.trim(),
        description: description.trim() || undefined,
        priority,
        contact_id: Number(contactId),
      },
      {
        onSuccess: (ticket) => navigate(`/support/${ticket.id}`),
      },
    )
  }

  return (
    <Box sx={{ p: 3, maxWidth: 600 }}>
      <Button component={Link} to="/support" sx={{ mb: 2 }}>
        ← Back to queue
      </Button>
      <Typography variant="h5" mb={2}>New Support Ticket</Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {(error as Error).message}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <TextField
            label="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
            fullWidth
            disabled={isPending}
          />

          <TextField
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            multiline
            minRows={3}
            fullWidth
            disabled={isPending}
          />

          <FormControl fullWidth>
            <InputLabel>Priority</InputLabel>
            <Select
              label="Priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              disabled={isPending}
            >
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Contact ID"
            type="number"
            value={contactId}
            onChange={(e) => setContactId(e.target.value)}
            required
            fullWidth
            disabled={isPending}
          />

          <Button type="submit" variant="contained" disabled={isPending || !subject.trim() || !contactId}>
            {isPending ? <CircularProgress size={20} /> : 'Create Ticket'}
          </Button>
        </Stack>
      </Box>
    </Box>
  )
}
