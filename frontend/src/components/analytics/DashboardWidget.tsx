import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Typography from '@mui/material/Typography'
import type { DashboardWidget as DashboardWidgetType } from '../../types/analytics'

interface Props {
  widget: DashboardWidgetType
}

export default function DashboardWidget({ widget }: Props) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h4" component="div">
          {widget.unit === '$'
            ? `$${Number(widget.value).toLocaleString()}`
            : widget.value.toLocaleString()}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {widget.label}
        </Typography>
      </CardContent>
    </Card>
  )
}
