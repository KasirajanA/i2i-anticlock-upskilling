import Timeline from '@mui/lab/Timeline'
import TimelineConnector from '@mui/lab/TimelineConnector'
import TimelineContent from '@mui/lab/TimelineContent'
import TimelineDot from '@mui/lab/TimelineDot'
import TimelineItem from '@mui/lab/TimelineItem'
import TimelineOppositeContent from '@mui/lab/TimelineOppositeContent'
import TimelineSeparator from '@mui/lab/TimelineSeparator'
import Chip from '@mui/material/Chip'
import Typography from '@mui/material/Typography'
import type { ActivityLog } from '../../types/contracts'

interface Props {
  logs: ActivityLog[]
}

const ACTION_TYPE_LABELS: Record<string, string> = {
  status_transition: 'Status Change',
  edit: 'Edit',
  attachment_added: 'Attachment Added',
  attachment_removed: 'Attachment Removed',
  renewal_flagged: 'Renewal Due',
  renewed: 'Renewed',
}

export default function ContractActivityLog({ logs }: Props) {
  if (logs.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No activity recorded yet.
      </Typography>
    )
  }

  return (
    <Timeline position="right" aria-label="Contract activity log">
      {logs.map((log, i) => (
        <TimelineItem key={log.id}>
          <TimelineOppositeContent
            sx={{ flex: 0.3, py: '12px' }}
            variant="body2"
            color="text.secondary"
          >
            {new Date(log.created_at).toLocaleString()}
          </TimelineOppositeContent>
          <TimelineSeparator>
            <TimelineDot color="primary" />
            {i < logs.length - 1 && <TimelineConnector />}
          </TimelineSeparator>
          <TimelineContent sx={{ py: '12px', px: 2 }}>
            <Chip
              label={ACTION_TYPE_LABELS[log.action_type] ?? log.action_type}
              size="small"
              variant="outlined"
            />
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {log.actor_name}
            </Typography>
            {log.note && (
              <Typography variant="caption" color="text.secondary">
                {log.note}
              </Typography>
            )}
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  )
}
