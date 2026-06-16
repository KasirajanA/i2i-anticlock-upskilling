import AutorenewIcon from '@mui/icons-material/Autorenew'
import Badge from '@mui/material/Badge'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import FormControl from '@mui/material/FormControl'
import Grid from '@mui/material/Grid'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { DataGrid, type GridColDef, type GridPaginationModel } from '@mui/x-data-grid'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { ContractFilterParams, ContractStatus } from '../../types/contracts'
import { useContracts, useRenewContract } from '../../hooks/useContracts'
import ContractStatusChip from './ContractStatusChip'
import Button from '@mui/material/Button'
import Alert from '@mui/material/Alert'

const STATUSES: ContractStatus[] = [
  'Draft',
  'Sent for Review',
  'Active',
  'Expired',
  'Terminated',
]

interface RenewButtonProps {
  refId: string
  disabled?: boolean
}

function RenewButton({ refId, disabled }: RenewButtonProps) {
  const { mutate, isPending, isError, error } = useRenewContract(refId)
  return (
    <Tooltip title={isError ? (error as Error).message : 'Create renewal draft'}>
      <span>
        <Button
          size="small"
          variant="outlined"
          startIcon={<AutorenewIcon />}
          onClick={(e) => { e.stopPropagation(); mutate() }}
          disabled={disabled || isPending}
          aria-label={`Renew contract ${refId}`}
        >
          Renew
        </Button>
      </span>
    </Tooltip>
  )
}

interface Props {
  userRole?: string
}

export default function ContractList({ userRole = 'Sales Rep' }: Props) {
  const [filters, setFilters] = useState<ContractFilterParams>({
    page: 1,
    limit: 20,
  })
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 20,
  })

  const { data, isLoading, isError, error } = useContracts({
    ...filters,
    page: paginationModel.page + 1,
    limit: paginationModel.pageSize,
  })

  const columns: GridColDef[] = [
    {
      field: 'ref_id',
      headerName: 'Reference',
      width: 120,
      renderCell: (p) => (
        <Link
          to={`/contracts/${p.value}`}
          aria-label={`Open contract ${p.value}`}
        >
          {p.value}
        </Link>
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 160,
      renderCell: (p) => <ContractStatusChip status={p.value as ContractStatus} />,
    },
    { field: 'value', headerName: 'Value', width: 130 },
    { field: 'start_date', headerName: 'Start', width: 110 },
    { field: 'end_date', headerName: 'End', width: 110 },
    {
      field: 'is_renewal_due',
      headerName: 'Renewal',
      width: 100,
      renderCell: (p) =>
        p.value ? (
          <Tooltip title="Renewal due">
            <Badge color="warning" variant="dot">
              <AutorenewIcon color="warning" fontSize="small" />
            </Badge>
          </Tooltip>
        ) : null,
    },
    {
      field: 'actions',
      headerName: '',
      width: 130,
      sortable: false,
      renderCell: (p) =>
        p.row.status === 'Active' && (
          <RenewButton refId={p.row.ref_id} />
        ),
    },
  ]

  if (isError) {
    return (
      <Alert severity="error">
        {(error as Error).message}
      </Alert>
    )
  }

  return (
    <Box>
      {/* Filter toolbar */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Status</InputLabel>
            <Select
              value={filters.status ?? ''}
              label="Status"
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  status: (e.target.value as ContractStatus) || undefined,
                }))
              }
            >
              <MenuItem value="">All</MenuItem>
              {STATUSES.map((s) => (
                <MenuItem key={s} value={s}>
                  {s}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={3}>
          <TextField
            label="Account ID"
            size="small"
            fullWidth
            type="number"
            value={filters.account_id ?? ''}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                account_id: e.target.value ? Number(e.target.value) : undefined,
              }))
            }
            inputProps={{ 'aria-label': 'Filter by account ID' }}
          />
        </Grid>
        <Grid item xs={12} sm={3}>
          <TextField
            label="End date from"
            size="small"
            fullWidth
            type="date"
            InputLabelProps={{ shrink: true }}
            value={filters.end_date_from ?? ''}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                end_date_from: e.target.value || undefined,
              }))
            }
            inputProps={{ 'aria-label': 'Filter end date from' }}
          />
        </Grid>
        <Grid item xs={12} sm={3}>
          <TextField
            label="End date to"
            size="small"
            fullWidth
            type="date"
            InputLabelProps={{ shrink: true }}
            value={filters.end_date_to ?? ''}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                end_date_to: e.target.value || undefined,
              }))
            }
            inputProps={{ 'aria-label': 'Filter end date to' }}
          />
        </Grid>
      </Grid>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress aria-label="Loading contracts" />
        </Box>
      )}

      {!isLoading && (
        <DataGrid
          rows={data?.items ?? []}
          columns={columns}
          rowCount={data?.total ?? 0}
          paginationMode="server"
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          pageSizeOptions={[20, 50, 100]}
          getRowId={(row) => row.id}
          autoHeight
          disableRowSelectionOnClick
          aria-label="Contracts list"
        />
      )}
    </Box>
  )
}
