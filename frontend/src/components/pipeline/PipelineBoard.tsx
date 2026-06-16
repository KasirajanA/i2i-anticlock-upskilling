import AddIcon from '@mui/icons-material/Add'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Typography from '@mui/material/Typography'
import { useState } from 'react'
import { useDeals } from '../../hooks/useDeals'
import { useStageChange } from '../../hooks/useStageChange'
import { usePipelineFilters } from '../../store/pipelineFilters'
import type { DealStage, DealSummary } from '../../types/deal'
import { DEAL_STAGES } from '../../types/deal'
import DealDetailPanel from './DealDetailPanel'
import DealForm from './DealForm'
import StageChangeModal from './StageChangeModal'
import StageColumn from './StageColumn'

export default function PipelineBoard() {
  const filters = usePipelineFilters()
  const { data, isLoading } = useDeals({
    stage: filters.stage,
    owner_id: filters.owner_id,
    account_id: filters.account_id,
    is_overdue: filters.is_overdue,
    close_date_from: filters.close_date_from,
    close_date_to: filters.close_date_to,
    limit: 200,
  })

  const stageChange = useStageChange()
  const [selected, setSelected] = useState<DealSummary | null>(null)
  const [pending, setPending] = useState<{ refId: string; stage: DealStage } | null>(null)
  const [formOpen, setFormOpen] = useState(false)

  function handleDrop(refId: string, targetStage: DealStage) {
    const deal = data?.items.find((d) => d.ref_id === refId)
    if (!deal || deal.stage === targetStage) return
    if (targetStage === 'Closed Lost') {
      setPending({ refId, stage: targetStage })
    } else {
      stageChange.mutate({ refId, payload: { stage: targetStage } })
    }
  }

  function handleStageConfirm(stage: DealStage, lossReason?: string) {
    if (!pending) return
    stageChange.mutate({
      refId: pending.refId,
      payload: { stage, loss_reason: lossReason },
    })
    setPending(null)
  }

  if (isLoading) return <CircularProgress sx={{ m: 4 }} />

  const byStage = (stage: DealStage): DealSummary[] =>
    data?.items.filter((d) => d.stage === stage) ?? []

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setFormOpen(true)}>
          New Deal
        </Button>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, overflowX: 'auto', pb: 2 }}>
        {DEAL_STAGES.map((stage) => (
          <StageColumn
            key={stage}
            stage={stage}
            deals={byStage(stage)}
            onSelect={setSelected}
            onDrop={handleDrop}
          />
        ))}
      </Box>
      {data && data.total === 0 && (
        <Typography color="text.secondary" sx={{ mt: 2 }}>
          No deals yet. Create one to get started.
        </Typography>
      )}
      <DealDetailPanel deal={selected} onClose={() => setSelected(null)} />
      <DealForm open={formOpen} onClose={() => setFormOpen(false)} />
      {pending && (
        <StageChangeModal
          open
          currentStage={pending.stage}
          onConfirm={handleStageConfirm}
          onClose={() => setPending(null)}
        />
      )}
    </Box>
  )
}
