import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import FormControl from '@mui/material/FormControl'
import FormHelperText from '@mui/material/FormHelperText'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import type { DealCreateRequest, DealStage } from '../../types/deal'
import { DEAL_STAGES } from '../../types/deal'
import { useCreateDeal } from '../../hooks/useDeals'

interface Props {
  open: boolean
  onClose: () => void
  defaultOwnerId?: number
  defaultAccountId?: number
}

interface FormState {
  title: string
  value: string
  stage: DealStage
  expected_close_date: string
  account_id: string
  owner_id: string
}

const EMPTY: FormState = {
  title: '',
  value: '',
  stage: 'Lead In',
  expected_close_date: '',
  account_id: '',
  owner_id: '',
}

function validate(f: FormState): Partial<Record<keyof FormState, string>> {
  const errs: Partial<Record<keyof FormState, string>> = {}
  if (!f.title.trim()) errs.title = 'Required'
  const v = Number(f.value)
  if (!f.value || isNaN(v) || v < 0) errs.value = 'Must be ≥ 0'
  if (!f.expected_close_date) errs.expected_close_date = 'Required'
  if (!f.account_id || isNaN(Number(f.account_id))) errs.account_id = 'Required'
  if (!f.owner_id || isNaN(Number(f.owner_id))) errs.owner_id = 'Required'
  return errs
}

export default function DealForm({ open, onClose, defaultOwnerId, defaultAccountId }: Props) {
  const [form, setForm] = useState<FormState>({
    ...EMPTY,
    owner_id: defaultOwnerId ? String(defaultOwnerId) : '',
    account_id: defaultAccountId ? String(defaultAccountId) : '',
  })
  const [touched, setTouched] = useState(false)
  const createDeal = useCreateDeal()

  const errors = validate(form)
  const hasErrors = Object.keys(errors).length > 0

  function set(field: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit() {
    setTouched(true)
    if (hasErrors) return
    const payload: DealCreateRequest = {
      title: form.title.trim(),
      value: form.value,
      stage: form.stage,
      expected_close_date: form.expected_close_date,
      account_id: Number(form.account_id),
      owner_id: Number(form.owner_id),
    }
    await createDeal.mutateAsync(payload)
    setForm(EMPTY)
    setTouched(false)
    onClose()
  }

  function handleClose() {
    setForm(EMPTY)
    setTouched(false)
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>New Deal</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
        <TextField
          label="Title"
          required
          value={form.title}
          onChange={(e) => set('title', e.target.value)}
          error={touched && Boolean(errors.title)}
          helperText={touched ? errors.title : undefined}
        />
        <TextField
          label="Value"
          required
          type="number"
          inputProps={{ min: 0, step: '0.01' }}
          value={form.value}
          onChange={(e) => set('value', e.target.value)}
          error={touched && Boolean(errors.value)}
          helperText={touched ? errors.value : undefined}
        />
        <FormControl required error={touched && Boolean(errors.stage)}>
          <InputLabel>Stage</InputLabel>
          <Select
            value={form.stage}
            label="Stage"
            onChange={(e) => set('stage', e.target.value as DealStage)}
          >
            {DEAL_STAGES.map((s) => (
              <MenuItem key={s} value={s}>
                {s}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          label="Close Date"
          required
          type="date"
          InputLabelProps={{ shrink: true }}
          value={form.expected_close_date}
          onChange={(e) => set('expected_close_date', e.target.value)}
          error={touched && Boolean(errors.expected_close_date)}
          helperText={touched ? errors.expected_close_date : undefined}
        />
        <TextField
          label="Account ID"
          required
          type="number"
          value={form.account_id}
          onChange={(e) => set('account_id', e.target.value)}
          error={touched && Boolean(errors.account_id)}
          helperText={touched ? errors.account_id : undefined}
        />
        <TextField
          label="Owner ID"
          required
          type="number"
          value={form.owner_id}
          onChange={(e) => set('owner_id', e.target.value)}
          error={touched && Boolean(errors.owner_id)}
          helperText={touched ? errors.owner_id : undefined}
        />
        {createDeal.isError && (
          <FormHelperText error>
            {(createDeal.error as Error).message}
          </FormHelperText>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={createDeal.isPending}
        >
          Create
        </Button>
      </DialogActions>
    </Dialog>
  )
}
