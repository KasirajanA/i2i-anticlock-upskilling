import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { useState } from 'react'
import type { DealStage, DealSummary } from '../../types/deal'
import DealCard from './DealCard'

interface Props {
  stage: DealStage
  deals: DealSummary[]
  onSelect: (deal: DealSummary) => void
  onDrop: (refId: string, targetStage: DealStage) => void
}

export default function StageColumn({ stage, deals, onSelect, onDrop }: Props) {
  const [dragOver, setDragOver] = useState(false)

  return (
    <Paper
      variant="outlined"
      sx={{
        minWidth: 220,
        flex: '0 0 220px',
        p: 1,
        bgcolor: dragOver ? 'action.hover' : 'background.paper',
        transition: 'background-color 0.15s',
      }}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        const refId = e.dataTransfer.getData('application/deal-ref-id')
        if (refId) onDrop(refId, stage)
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="subtitle1" fontWeight="bold">
          {stage}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {deals.length}
        </Typography>
      </Box>
      {deals.map((deal) => (
        <DealCard key={deal.ref_id} deal={deal} onSelect={onSelect} />
      ))}
    </Paper>
  )
}
