import Timeline from '@mui/lab/Timeline'
import TimelineItem from '@mui/lab/TimelineItem'
import TimelineSeparator from '@mui/lab/TimelineSeparator'
import TimelineDot from '@mui/lab/TimelineDot'
import TimelineConnector from '@mui/lab/TimelineConnector'
import TimelineContent from '@mui/lab/TimelineContent'
import Typography from '@mui/material/Typography'
import type { ActivityLogEntry } from '../../types/support'

interface Props {
  entries: ActivityLogEntry[]
}

export default function ActivityTimeline({ entries }: Props) {
  if (entries.length === 0) {
    return <Typography color="text.secondary">No activity yet.</Typography>
  }

  return (
    <Timeline>
      {entries.map((entry, i) => (
        <TimelineItem key={entry.id}>
          <TimelineSeparator>
            <TimelineDot color="primary" />
            {i < entries.length - 1 && <TimelineConnector />}
          </TimelineSeparator>
          <TimelineContent>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {entry.event_type.replace(/_/g, ' ')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {entry.actor_id ? `User #${entry.actor_id}` : 'System'} · {new Date(entry.created_at).toLocaleString()}
            </Typography>
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  )
}
