import { useState } from 'react'
import Box from '@mui/material/Box'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import FormControlLabel from '@mui/material/FormControlLabel'
import Switch from '@mui/material/Switch'
import CircularProgress from '@mui/material/CircularProgress'
import { useAddReply } from '../../hooks/useTicketMutations'

interface Props {
  ticketId: number
  isAgent: boolean
}

export default function ReplyForm({ ticketId, isAgent }: Props) {
  const [body, setBody] = useState('')
  const [isInternal, setIsInternal] = useState(false)
  const { mutate: addReply, isPending } = useAddReply(ticketId)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!body.trim()) return
    addReply(
      { body: body.trim(), is_internal: isAgent ? isInternal : false },
      { onSuccess: () => { setBody(''); setIsInternal(false) } },
    )
  }

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
      <TextField
        label="Reply"
        multiline
        minRows={3}
        value={body}
        onChange={(e) => setBody(e.target.value)}
        disabled={isPending}
        required
        fullWidth
      />
      {isAgent && (
        <FormControlLabel
          control={
            <Switch
              checked={isInternal}
              onChange={(e) => setIsInternal(e.target.checked)}
              disabled={isPending}
            />
          }
          label="Internal note"
        />
      )}
      <Box>
        <Button type="submit" variant="contained" disabled={isPending || !body.trim()}>
          {isPending ? <CircularProgress size={18} /> : 'Send'}
        </Button>
      </Box>
    </Box>
  )
}
