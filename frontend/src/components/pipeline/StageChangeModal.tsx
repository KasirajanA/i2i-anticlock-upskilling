import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import type { DealStage } from '../../types/deal'
import { DEAL_STAGES } from '../../types/deal'

interface Props {
  open: boolean
  currentStage: DealStage
  onConfirm: (stage: DealStage, lossReason?: string) => void
  onClose: () => void
}

export default function StageChangeModal({ open, currentStage, onConfirm, onClose }: Props) {
  const [stage, setStage] = useState<DealStage>(currentStage)
  const [lossReason, setLossReason] = useState('')

  const isClosedLost = stage === 'Closed Lost'

  function handleConfirm() {
    if (isClosedLost && !lossReason.trim()) return
    onConfirm(stage, isClosedLost ? lossReason : undefined)
    setLossReason('')
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Change Stage</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
        <FormControl fullWidth>
          <InputLabel>Stage</InputLabel>
          <Select
            value={stage}
            label="Stage"
            onChange={(e) => setStage(e.target.value as DealStage)}
          >
            {DEAL_STAGES.map((s) => (
              <MenuItem key={s} value={s}>
                {s}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {isClosedLost && (
          <TextField
            label="Loss Reason"
            multiline
            minRows={2}
            required
            value={lossReason}
            onChange={(e) => setLossReason(e.target.value)}
            error={!lossReason.trim()}
            helperText={!lossReason.trim() ? 'Required for Closed Lost' : undefined}
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleConfirm}
          disabled={isClosedLost && !lossReason.trim()}
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  )
}
