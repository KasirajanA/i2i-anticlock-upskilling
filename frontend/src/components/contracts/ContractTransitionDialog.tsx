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
import type { Contract, ContractStatus } from '../../types/contracts'
import { useTransitionContract } from '../../hooks/useContracts'
import Alert from '@mui/material/Alert'

const FORWARD_TRANSITIONS: Record<ContractStatus, ContractStatus[]> = {
  Draft: ['Sent for Review'],
  'Sent for Review': ['Active'],
  Active: ['Terminated'],
  Expired: [],
  Terminated: [],
}

const STATUS_ORDER: ContractStatus[] = [
  'Draft',
  'Sent for Review',
  'Active',
  'Expired',
  'Terminated',
]

function isBackward(from: ContractStatus, to: ContractStatus): boolean {
  return STATUS_ORDER.indexOf(to) < STATUS_ORDER.indexOf(from)
}

interface Props {
  open: boolean
  onClose: () => void
  contract: Contract
  userRole: string
}

export default function ContractTransitionDialog({
  open,
  onClose,
  contract,
  userRole,
}: Props) {
  const [targetStatus, setTargetStatus] = useState<ContractStatus | ''>('')
  const [note, setNote] = useState('')
  const transition = useTransitionContract(contract.ref_id)

  const isAdmin = userRole === 'Admin'

  const availableStatuses: ContractStatus[] = isAdmin
    ? STATUS_ORDER.filter((s) => s !== contract.status)
    : FORWARD_TRANSITIONS[contract.status] ?? []

  const requiresNote = targetStatus !== '' && isBackward(contract.status, targetStatus)

  function handleSubmit() {
    if (!targetStatus) return
    transition.mutate(
      { status: targetStatus, note: note || undefined },
      {
        onSuccess: () => {
          setTargetStatus('')
          setNote('')
          onClose()
        },
      },
    )
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Change Contract Status</DialogTitle>
      <DialogContent>
        {transition.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {(transition.error as Error).message}
          </Alert>
        )}

        <FormControl fullWidth sx={{ mt: 1 }}>
          <InputLabel id="status-select-label">New Status</InputLabel>
          <Select
            labelId="status-select-label"
            value={targetStatus}
            label="New Status"
            onChange={(e) => setTargetStatus(e.target.value as ContractStatus)}
          >
            {availableStatuses.map((s) => (
              <MenuItem key={s} value={s}>
                {s}
                {isAdmin && isBackward(contract.status, s) && ' (revert)'}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          label={requiresNote ? 'Note (required for revert)' : 'Note (optional)'}
          fullWidth
          multiline
          rows={3}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          required={requiresNote}
          sx={{ mt: 2 }}
          inputProps={{ 'aria-label': 'Transition note' }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={
            !targetStatus || (requiresNote && !note.trim()) || transition.isPending
          }
        >
          Apply
        </Button>
      </DialogActions>
    </Dialog>
  )
}
