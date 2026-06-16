import Chip from '@mui/material/Chip'
import type { TicketPriority } from '../../types/support'

const COLOR_MAP: Record<TicketPriority, 'default' | 'info' | 'warning' | 'error'> = {
  low: 'default',
  medium: 'info',
  high: 'warning',
  critical: 'error',
}

interface Props {
  priority: TicketPriority
}

export default function PriorityBadge({ priority }: Props) {
  return (
    <Chip
      label={priority.charAt(0).toUpperCase() + priority.slice(1)}
      color={COLOR_MAP[priority] ?? 'default'}
      size="small"
    />
  )
}
