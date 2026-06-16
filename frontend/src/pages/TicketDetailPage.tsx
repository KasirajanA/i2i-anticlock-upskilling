import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import { useParams, Link } from 'react-router-dom'
import TicketDetail from '../components/support/TicketDetail'

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const ticketId = Number(id)

  return (
    <Box sx={{ p: 3 }}>
      <Button component={Link} to="/support" sx={{ mb: 2 }}>
        ← Back to queue
      </Button>
      {ticketId > 0 ? (
        <TicketDetail ticketId={ticketId} isAgent />
      ) : (
        <div>Invalid ticket ID.</div>
      )}
    </Box>
  )
}
