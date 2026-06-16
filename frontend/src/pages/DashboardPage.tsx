import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { useDashboard } from '../hooks/useAnalytics'
import DashboardGrid from '../components/analytics/DashboardGrid'

export default function DashboardPage() {
  const { data, isLoading, isError } = useDashboard()

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', mb: 2 }}>
        <Typography variant="h5">Dashboard</Typography>
        {data && (
          <Typography variant="caption" color="text.secondary">
            Generated: {new Date(data.generated_at).toLocaleString()}
          </Typography>
        )}
      </Box>
      {isError && <Typography color="error">Failed to load dashboard.</Typography>}
      <DashboardGrid widgets={data?.widgets ?? []} loading={isLoading} />
    </Box>
  )
}
