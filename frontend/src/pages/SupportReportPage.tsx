import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Stack from '@mui/material/Stack'
import CircularProgress from '@mui/material/CircularProgress'
import { useSupportReport } from '../hooks/useAnalytics'
import type { ReportFilters, StatusBreakdown, PriorityBreakdown, PerAgentCount } from '../types/analytics'
import ReportFilterBar from '../components/analytics/ReportFilterBar'
import ReportTable, { type Column } from '../components/analytics/ReportTable'
import CacheTimer from '../components/analytics/CacheTimer'
import ExportButton from '../components/analytics/ExportButton'
import { exportSupportReport } from '../services/analyticsApi'

const statusColumns: Column<StatusBreakdown>[] = [
  { field: 'status', headerName: 'Status' },
  { field: 'count', headerName: 'Count' },
]

const priorityColumns: Column<PriorityBreakdown>[] = [
  { field: 'priority', headerName: 'Priority' },
  { field: 'count', headerName: 'Count' },
]

const agentColumns: Column<PerAgentCount>[] = [
  { field: 'assignee_name', headerName: 'Agent' },
  { field: 'count', headerName: 'Tickets' },
]

export default function SupportReportPage() {
  const [filters, setFilters] = useState<ReportFilters>({})
  const { data, isLoading, isError } = useSupportReport(filters)

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Support Report</Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <CacheTimer cached_until={data?.cached_until ?? null} />
          <ExportButton onExport={() => exportSupportReport(filters)} />
        </Stack>
      </Stack>
      <ReportFilterBar filters={filters} onChange={setFilters} showOwnerFilter />
      {isLoading && <CircularProgress />}
      {isError && <Typography color="error">Failed to load report.</Typography>}
      {data && (
        <>
          <Stack direction="row" spacing={4} mb={2}>
            {data.avg_resolution_hours != null && (
              <Typography>Avg Resolution: <strong>{data.avg_resolution_hours.toFixed(1)}h</strong></Typography>
            )}
            {data.sla_breach_rate != null && (
              <Typography>SLA Breach Rate: <strong>{(data.sla_breach_rate * 100).toFixed(1)}%</strong></Typography>
            )}
          </Stack>
          <ReportTable<StatusBreakdown> title="By Status" columns={statusColumns} rows={data.status_breakdown} />
          <ReportTable<PriorityBreakdown> title="By Priority" columns={priorityColumns} rows={data.priority_breakdown} />
          <ReportTable<PerAgentCount> title="Per Agent" columns={agentColumns} rows={data.per_agent} />
        </>
      )}
    </Box>
  )
}
