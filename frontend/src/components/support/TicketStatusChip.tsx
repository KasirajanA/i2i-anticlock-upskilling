import Chip from '@mui/material/Chip'
import type { TicketStatus } from '../../types/support'

const COLOR_MAP: Record<TicketStatus, 'default' | 'info' | 'warning' | 'success'> = {
  open: 'info',
  in_progress: 'warning',
  resolved: 'success',
  closed: 'default',
}

const LABEL_MAP: Record<TicketStatus, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  resolved: 'Resolved',
  closed: 'Closed',
}

interface Props {
  status: TicketStatus
}

export default function TicketStatusChip({ status }: Props) {
  return (
    <Chip
      label={LABEL_MAP[status] ?? status}
      color={COLOR_MAP[status] ?? 'default'}
      size="small"
    />
  )
}
