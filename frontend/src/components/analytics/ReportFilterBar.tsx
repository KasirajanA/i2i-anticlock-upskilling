import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import type { ReportFilters } from '../../types/analytics'

interface Props {
  filters: ReportFilters
  onChange: (f: ReportFilters) => void
  showOwnerFilter?: boolean
}

export default function ReportFilterBar({ filters, onChange, showOwnerFilter = false }: Props) {
  return (
    <Box sx={{ mb: 2 }}>
      <Stack direction="row" spacing={2} flexWrap="wrap">
        <TextField
          label="From"
          type="date"
          size="small"
          InputLabelProps={{ shrink: true }}
          value={filters.created_after ?? ''}
          onChange={(e) => onChange({ ...filters, created_after: e.target.value || undefined })}
        />
        <TextField
          label="To"
          type="date"
          size="small"
          InputLabelProps={{ shrink: true }}
          value={filters.created_before ?? ''}
          onChange={(e) => onChange({ ...filters, created_before: e.target.value || undefined })}
        />
        {showOwnerFilter && (
          <TextField
            label="Owner ID"
            type="number"
            size="small"
            value={filters.owner_id ?? ''}
            onChange={(e) =>
              onChange({ ...filters, owner_id: e.target.value ? Number(e.target.value) : undefined })
            }
          />
        )}
      </Stack>
    </Box>
  )
}
