import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Stack from '@mui/material/Stack'
import CircularProgress from '@mui/material/CircularProgress'
import { useSalesReport } from '../hooks/useAnalytics'
import type { ReportFilters, StageBreakdown, RepRevenue } from '../types/analytics'
import ReportFilterBar from '../components/analytics/ReportFilterBar'
import ReportTable, { type Column } from '../components/analytics/ReportTable'
import CacheTimer from '../components/analytics/CacheTimer'
import ExportButton from '../components/analytics/ExportButton'
import { exportSalesReport } from '../services/analyticsApi'

const stageColumns: Column<StageBreakdown>[] = [
  { field: 'stage', headerName: 'Stage' },
  { field: 'count', headerName: 'Count' },
  { field: 'total_value', headerName: 'Total Value' },
]

const repColumns: Column<RepRevenue>[] = [
  { field: 'owner_name', headerName: 'Rep' },
  { field: 'revenue', headerName: 'Revenue' },
]

export default function SalesReportPage() {
  const [filters, setFilters] = useState<ReportFilters>({})
  const { data, isLoading, isError } = useSalesReport(filters)

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Sales Report</Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <CacheTimer cached_until={data?.cached_until ?? null} />
          <ExportButton onExport={() => exportSalesReport(filters)} />
        </Stack>
      </Stack>
      <ReportFilterBar filters={filters} onChange={setFilters} showOwnerFilter />
      {isLoading && <CircularProgress />}
      {isError && <Typography color="error">Failed to load report.</Typography>}
      {data && (
        <>
          <Stack direction="row" spacing={4} mb={2}>
            <Typography>Won: <strong>{data.won_count}</strong></Typography>
            <Typography>Lost: <strong>{data.lost_count}</strong></Typography>
            {data.avg_deal_value && (
              <Typography>Avg Deal: <strong>${data.avg_deal_value}</strong></Typography>
            )}
          </Stack>
          <ReportTable<StageBreakdown> title="Stage Breakdown" columns={stageColumns} rows={data.stage_breakdown} />
          <ReportTable<RepRevenue> title="Top Reps by Revenue" columns={repColumns} rows={data.top_reps} />
        </>
      )}
    </Box>
  )
}
