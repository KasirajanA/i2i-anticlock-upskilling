import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Grid from '@mui/material/Grid'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import type { ContractCreateRequest, ContractUpdateRequest } from '../../types/contracts'
import Alert from '@mui/material/Alert'

interface Props {
  mode: 'create' | 'edit'
  initialValues?: Partial<ContractCreateRequest>
  onSubmit: (data: ContractCreateRequest | ContractUpdateRequest) => void
  isLoading?: boolean
  error?: string | null
}

interface FormErrors {
  value?: string
  start_date?: string
  end_date?: string
  account_id?: string
}

export default function ContractForm({
  mode,
  initialValues = {},
  onSubmit,
  isLoading = false,
  error = null,
}: Props) {
  const [value, setValue] = useState(String(initialValues.value ?? ''))
  const [startDate, setStartDate] = useState(initialValues.start_date ?? '')
  const [endDate, setEndDate] = useState(initialValues.end_date ?? '')
  const [description, setDescription] = useState(initialValues.description ?? '')
  const [accountId, setAccountId] = useState(String(initialValues.account_id ?? ''))
  const [dealId, setDealId] = useState(String(initialValues.deal_id ?? ''))
  const [errors, setErrors] = useState<FormErrors>({})

  function validate(): boolean {
    const next: FormErrors = {}
    if (!value || Number(value) <= 0) next.value = 'Value must be greater than 0'
    if (mode === 'create' && !accountId) next.account_id = 'Account is required'
    if (!startDate) next.start_date = 'Start date is required'
    if (!endDate) next.end_date = 'End date is required'
    if (startDate && endDate && endDate < startDate) {
      next.end_date = 'End date must be on or after start date'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    const payload = {
      value: Number(value),
      start_date: startDate,
      end_date: endDate,
      description: description || undefined,
      ...(mode === 'create' ? { account_id: Number(accountId) } : {}),
      ...(dealId ? { deal_id: Number(dealId) } : {}),
    }
    onSubmit(payload)
  }

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        {mode === 'create' && (
          <Grid item xs={12} sm={6}>
            <TextField
              label="Account ID"
              fullWidth
              required
              type="number"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              error={Boolean(errors.account_id)}
              helperText={errors.account_id}
              inputProps={{ 'aria-label': 'Account ID' }}
            />
          </Grid>
        )}

        <Grid item xs={12} sm={6}>
          <TextField
            label="Contract Value"
            fullWidth
            required
            type="number"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            error={Boolean(errors.value)}
            helperText={errors.value}
            inputProps={{ min: 0.01, step: 0.01, 'aria-label': 'Contract value' }}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            label="Start Date"
            fullWidth
            required
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            error={Boolean(errors.start_date)}
            helperText={errors.start_date}
            InputLabelProps={{ shrink: true }}
            inputProps={{ 'aria-label': 'Start date' }}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            label="End Date"
            fullWidth
            required
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            error={Boolean(errors.end_date)}
            helperText={errors.end_date}
            InputLabelProps={{ shrink: true }}
            inputProps={{ 'aria-label': 'End date' }}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            label="Deal ID (optional)"
            fullWidth
            type="number"
            value={dealId}
            onChange={(e) => setDealId(e.target.value)}
            inputProps={{ 'aria-label': 'Deal ID' }}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            inputProps={{ 'aria-label': 'Contract description' }}
          />
        </Grid>

        <Grid item xs={12}>
          <Button
            type="submit"
            variant="contained"
            disabled={isLoading}
            startIcon={isLoading ? <CircularProgress size={18} /> : null}
          >
            {mode === 'create' ? 'Create Contract' : 'Save Changes'}
          </Button>
        </Grid>
      </Grid>
    </Box>
  )
}
