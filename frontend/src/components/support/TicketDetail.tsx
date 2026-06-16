import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import Stack from '@mui/material/Stack'
import CircularProgress from '@mui/material/CircularProgress'
import Paper from '@mui/material/Paper'
import { useQuery } from '@tanstack/react-query'
import { useTicket } from '../../hooks/useTickets'
import { listReplies, getActivity } from '../../services/supportApi'
import TicketStatusChip from './TicketStatusChip'
import PriorityBadge from './PriorityBadge'
import ReplyForm from './ReplyForm'
import ActivityTimeline from './ActivityTimeline'
import type { Reply } from '../../types/support'

interface Props {
  ticketId: number
  isAgent: boolean
}

export default function TicketDetail({ ticketId, isAgent }: Props) {
  const { data: ticket, isLoading, isError } = useTicket(ticketId)
  const { data: repliesData } = useQuery({
    queryKey: ['replies', ticketId],
    queryFn: () => listReplies(ticketId),
    enabled: ticketId > 0,
  })
  const { data: activityData } = useQuery({
    queryKey: ['activity', ticketId],
    queryFn: () => getActivity(ticketId),
    enabled: ticketId > 0,
  })
  const replies = repliesData?.items ?? []
  const activity = activityData?.items ?? []

  if (isLoading) return <CircularProgress />
  if (isError || !ticket) return <Typography color="error">Ticket not found.</Typography>

  return (
    <Box>
      <Stack direction="row" spacing={1} alignItems="center" mb={1}>
        <Typography variant="h6" sx={{ flex: 1 }}>
          [{ticket.ref}] {ticket.subject}
        </Typography>
        <TicketStatusChip status={ticket.status} />
        <PriorityBadge priority={ticket.priority} />
      </Stack>

      <Typography variant="body2" color="text.secondary" mb={2}>
        {ticket.description ?? 'No description provided.'}
      </Typography>

      <Divider sx={{ my: 2 }} />

      <Typography variant="subtitle2" mb={1}>Replies</Typography>
      {replies.map((r: Reply) => (
        <Paper key={r.id} variant="outlined" sx={{ p: 1.5, mb: 1, bgcolor: r.is_internal ? 'action.hover' : 'background.paper' }}>
          <Typography variant="caption" color="text.secondary">
            {r.is_internal ? '[Internal] ' : ''}
            {new Date(r.created_at).toLocaleString()}
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>{r.body}</Typography>
        </Paper>
      ))}

      <ReplyForm ticketId={ticketId} isAgent={isAgent} />

      <Divider sx={{ my: 2 }} />

      <Typography variant="subtitle2" mb={1}>Activity</Typography>
      <ActivityTimeline entries={activity} />
    </Box>
  )
}
