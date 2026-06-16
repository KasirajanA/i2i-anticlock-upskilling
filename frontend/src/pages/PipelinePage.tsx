import Box from '@mui/material/Box'
import FormControlLabel from '@mui/material/FormControlLabel'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import PipelineBoard from '../components/pipeline/PipelineBoard'
import { usePipelineFilters } from '../store/pipelineFilters'

export default function PipelinePage() {
  const filters = usePipelineFilters()

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Sales Pipeline
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          label="Owner ID"
          size="small"
          type="number"
          sx={{ width: 120 }}
          value={filters.owner_id ?? ''}
          onChange={(e) =>
            filters.setOwnerId(e.target.value ? Number(e.target.value) : undefined)
          }
        />
        <TextField
          label="Account ID"
          size="small"
          type="number"
          sx={{ width: 120 }}
          value={filters.account_id ?? ''}
          onChange={(e) =>
            filters.setAccountId(e.target.value ? Number(e.target.value) : undefined)
          }
        />
        <TextField
          label="Close From"
          size="small"
          type="date"
          InputLabelProps={{ shrink: true }}
          value={filters.close_date_from ?? ''}
          onChange={(e) => filters.setCloseDateFrom(e.target.value || undefined)}
        />
        <TextField
          label="Close To"
          size="small"
          type="date"
          InputLabelProps={{ shrink: true }}
          value={filters.close_date_to ?? ''}
          onChange={(e) => filters.setCloseDateTo(e.target.value || undefined)}
        />
        <FormControlLabel
          control={
            <Switch
              checked={filters.is_overdue === true}
              onChange={(e) => filters.setIsOverdue(e.target.checked ? true : undefined)}
            />
          }
          label="Overdue only"
        />
      </Box>
      <PipelineBoard />
    </Box>
  )
}
