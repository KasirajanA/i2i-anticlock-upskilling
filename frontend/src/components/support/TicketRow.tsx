import TableRow from '@mui/material/TableRow'
import TableCell from '@mui/material/TableCell'
import { Link } from 'react-router-dom'
import type { TicketSummary } from '../../types/support'
import TicketStatusChip from './TicketStatusChip'
import PriorityBadge from './PriorityBadge'
import SLAIndicator from './SLAIndicator'

interface Props {
  ticket: TicketSummary
}

export default function TicketRow({ ticket }: Props) {
  return (
    <TableRow hover>
      <TableCell>
        <Link to={`/support/${ticket.id}`} style={{ textDecoration: 'none', fontWeight: 600 }}>
          {ticket.ref}
        </Link>
      </TableCell>
      <TableCell>{ticket.subject}</TableCell>
      <TableCell>
        <TicketStatusChip status={ticket.status} />
      </TableCell>
      <TableCell>
        <PriorityBadge priority={ticket.priority} />
      </TableCell>
      <TableCell>{ticket.contact_name ?? '—'}</TableCell>
      <TableCell>{ticket.assignee_id ? `#${ticket.assignee_id}` : 'Unassigned'}</TableCell>
      <TableCell>
        <SLAIndicator sla={ticket.sla ?? null} />
      </TableCell>
      <TableCell>{new Date(ticket.created_at).toLocaleDateString()}</TableCell>
    </TableRow>
  )
}
