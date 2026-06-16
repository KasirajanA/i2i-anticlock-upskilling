import Paper from '@mui/material/Paper'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Typography from '@mui/material/Typography'
import type { ForecastResponse } from '../../types/deal'

interface Props {
  data: ForecastResponse
}

function fmt(v: string) {
  return `$${Number(v).toFixed(2)}`
}

function pct(v: string) {
  return `${(Number(v) * 100).toFixed(0)}%`
}

export default function ForecastTable({ data }: Props) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Stage</TableCell>
            <TableCell align="right">Deals</TableCell>
            <TableCell align="right">Total Value</TableCell>
            <TableCell align="right">Probability</TableCell>
            <TableCell align="right">Weighted Value</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.open_pipeline.map((row) => (
            <TableRow key={row.stage}>
              <TableCell>{row.stage}</TableCell>
              <TableCell align="right">{row.deal_count}</TableCell>
              <TableCell align="right">{fmt(row.total_value)}</TableCell>
              <TableCell align="right">{pct(row.probability)}</TableCell>
              <TableCell align="right">{fmt(row.weighted_value)}</TableCell>
            </TableRow>
          ))}
          <TableRow sx={{ bgcolor: 'success.light' }}>
            <TableCell>
              <Typography fontWeight="bold">Closed Won</Typography>
            </TableCell>
            <TableCell align="right">{data.closed_won.deal_count}</TableCell>
            <TableCell align="right">{fmt(data.closed_won.total_value)}</TableCell>
            <TableCell align="right">100%</TableCell>
            <TableCell align="right">{fmt(data.closed_won.total_value)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell colSpan={4}>
              <Typography fontWeight="bold">Total Weighted Forecast</Typography>
            </TableCell>
            <TableCell align="right">
              <Typography fontWeight="bold">{fmt(data.total_weighted_forecast)}</Typography>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}
