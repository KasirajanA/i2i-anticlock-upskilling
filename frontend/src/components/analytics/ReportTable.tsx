import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import TableContainer from '@mui/material/TableContainer'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

export interface Column<T> {
  field: keyof T
  headerName: string
  renderCell?: (row: T) => React.ReactNode
}

interface Props<T extends Record<string, unknown>> {
  columns: Column<T>[]
  rows: T[]
  title?: string
}

export default function ReportTable<T extends Record<string, unknown>>({ columns, rows, title }: Props<T>) {
  return (
    <>
      {title && <Typography variant="subtitle1" sx={{ mt: 2, mb: 0.5, fontWeight: 600 }}>{title}</Typography>}
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((c) => (
                <TableCell key={String(c.field)}>{c.headerName}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} align="center">No data.</TableCell>
              </TableRow>
            ) : (
              rows.map((row, i) => (
                <TableRow key={i} sx={{ '&:last-child td': { border: 0 } }}>
                  {columns.map((c) => (
                    <TableCell key={String(c.field)}>
                      {c.renderCell
                        ? c.renderCell(row)
                        : String(row[c.field] ?? '')}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
