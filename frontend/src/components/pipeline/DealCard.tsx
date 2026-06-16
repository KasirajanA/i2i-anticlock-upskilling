import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import Card from '@mui/material/Card'
import CardActionArea from '@mui/material/CardActionArea'
import CardContent from '@mui/material/CardContent'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import type { DealSummary } from '../../types/deal'

interface Props {
  deal: DealSummary
  onSelect: (deal: DealSummary) => void
}

export default function DealCard({ deal, onSelect }: Props) {
  const formatted = Number(deal.value).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  })

  return (
    <Card
      variant="outlined"
      sx={{ mb: 1 }}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('application/deal-ref-id', deal.ref_id)
      }}
    >
      <CardActionArea onClick={() => onSelect(deal)}>
        <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
          <Typography variant="subtitle2" noWrap>
            {deal.is_overdue && (
              <Tooltip title="Overdue">
                <WarningAmberIcon
                  aria-label="Overdue"
                  fontSize="small"
                  color="warning"
                  sx={{ verticalAlign: 'middle', mr: 0.5 }}
                />
              </Tooltip>
            )}
            {deal.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {deal.account.name}
          </Typography>
          <Typography variant="body2">{formatted}</Typography>
          <Typography variant="caption" color="text.secondary">
            Close: {deal.expected_close_date}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  )
}
