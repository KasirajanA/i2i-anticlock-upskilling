import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Stack from '@mui/material/Stack'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import CircularProgress from '@mui/material/CircularProgress'
import { useContractReport } from '../hooks/useAnalytics'
import type { ContractFilters, UpcomingRenewal, AccountValue } from '../types/analytics'
import ReportTable, { type Column } from '../components/analytics/ReportTable'
import CacheTimer from '../components/analytics/CacheTimer'
import ExportButton from '../components/analytics/ExportButton'
import { exportContractReport } from '../services/analyticsApi'

const renewalColumns: Column<UpcomingRenewal>[] = [
  { field: 'ref_id', headerName: 'Ref' },
  { field: 'account_name', headerName: 'Account' },
  { field: 'value', headerName: 'Value' },
  { field: 'expiry_date', headerName: 'Expires' },
  { field: 'days_remaining', headerName: 'Days Left' },
]

const accountColumns: Column<AccountValue>[] = [
  { field: 'account_name', headerName: 'Account' },
  { field: 'total_value', headerName: 'Total Value' },
]

export default function ContractReportPage() {
  const [filters, setFilters] = useState<ContractFilters>({ renewal_window: 30 })
  const { data, isLoading, isError } = useContractReport(filters)

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Contract Report</Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <CacheTimer cached_until={data?.cached_until ?? null} />
          <ExportButton onExport={() => exportContractReport(filters)} />
        </Stack>
      </Stack>

      <FormControl size="small" sx={{ mb: 2, minWidth: 140 }}>
        <InputLabel>Renewal Window</InputLabel>
        <Select
          label="Renewal Window"
          value={filters.renewal_window ?? 30}
          onChange={(e) => setFilters({ ...filters, renewal_window: Number(e.target.value) as 30 | 60 | 90 })}
        >
          <MenuItem value={30}>30 days</MenuItem>
          <MenuItem value={60}>60 days</MenuItem>
          <MenuItem value={90}>90 days</MenuItem>
        </Select>
      </FormControl>

      {isLoading && <CircularProgress />}
      {isError && <Typography color="error">Failed to load report.</Typography>}
      {data && (
        <>
          <ReportTable title="Upcoming Renewals" columns={renewalColumns} rows={data.upcoming_renewals} />
          <ReportTable title="Value by Account" columns={accountColumns} rows={data.value_by_account} />
        </>
      )}
    </Box>
  )
}
