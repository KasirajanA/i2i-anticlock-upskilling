import Grid from '@mui/material/Grid'
import Skeleton from '@mui/material/Skeleton'
import type { DashboardWidget as DashboardWidgetType } from '../../types/analytics'
import DashboardWidget from './DashboardWidget'

interface Props {
  widgets: DashboardWidgetType[]
  loading?: boolean
}

export default function DashboardGrid({ widgets, loading = false }: Props) {
  if (loading) {
    return (
      <Grid container spacing={2}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Grid key={i} size={{ xs: 12, sm: 6, md: 3 }}>
            <Skeleton variant="rectangular" height={100} />
          </Grid>
        ))}
      </Grid>
    )
  }

  return (
    <Grid container spacing={2}>
      {widgets.map((w) => (
        <Grid key={w.key} size={{ xs: 12, sm: 6, md: 3 }}>
          <DashboardWidget widget={w} />
        </Grid>
      ))}
    </Grid>
  )
}
