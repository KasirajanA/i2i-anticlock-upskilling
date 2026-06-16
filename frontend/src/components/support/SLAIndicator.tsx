import Chip from '@mui/material/Chip'
import type { SLASummary } from '../../types/support'

interface Props {
  sla: SLASummary | null
}

export default function SLAIndicator({ sla }: Props) {
  if (!sla) return null

  if (sla.first_response_breached) {
    return <Chip label="Breached" color="error" size="small" aria-label="SLA Breached" />
  }

  const due = new Date(sla.first_response_due)
  const now = new Date()
  const diffMs = due.getTime() - now.getTime()
  const diffHours = diffMs / (1000 * 60 * 60)

  if (diffMs <= 0) {
    return <Chip label="Breached" color="error" size="small" aria-label="SLA Breached" />
  }

  if (diffHours < 1) {
    return <Chip label="Warning" color="warning" size="small" aria-label="SLA Warning" />
  }

  const mins = Math.round(diffMs / 60000)
  const label = mins >= 60 ? `${Math.floor(mins / 60)}h` : `${mins}m`
  return <Chip label={label} color="success" size="small" aria-label="SLA OK" />
}
