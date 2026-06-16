import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Paper from '@mui/material/Paper'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Typography from '@mui/material/Typography'
import { useTickets } from '../../hooks/useTickets'
import type { TicketFilters } from '../../types/support'
import TicketRow from './TicketRow'

interface Props {
  filters?: TicketFilters
}

export default function TicketQueue({ filters = {} }: Props) {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, isError } =
    useTickets(filters)

  if (isLoading) return <CircularProgress />
  if (isError) return <Typography color="error">Failed to load tickets.</Typography>

  const tickets = data?.pages.flatMap((p) => p.items) ?? []

  return (
    <>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Ref</TableCell>
              <TableCell>Subject</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell>Contact</TableCell>
              <TableCell>Assignee</TableCell>
              <TableCell>SLA</TableCell>
              <TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tickets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No tickets found.
                </TableCell>
              </TableRow>
            ) : (
              tickets.map((t) => <TicketRow key={t.id} ticket={t} />)
            )}
          </TableBody>
        </Table>
      </TableContainer>
      {hasNextPage && (
        <Button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
          sx={{ mt: 1 }}
        >
          {isFetchingNextPage ? 'Loading…' : 'Load more'}
        </Button>
      )}
    </>
  )
}
