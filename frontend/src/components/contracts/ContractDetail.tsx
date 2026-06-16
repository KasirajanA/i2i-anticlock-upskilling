import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import Grid from '@mui/material/Grid'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { useState } from 'react'
import type { Contract } from '../../types/contracts'
import { useActivityLog, useMutateContract } from '../../hooks/useContracts'
import ContractActivityLog from './ContractActivityLog'
import ContractAttachmentPanel from './ContractAttachmentPanel'
import ContractStatusChip from './ContractStatusChip'
import ContractTransitionDialog from './ContractTransitionDialog'

interface Props {
  contract: Contract
  userRole?: string
  userId?: number
}

const EDITABLE_STATUSES = ['Draft', 'Sent for Review'] as const

export default function ContractDetail({
  contract,
  userRole = 'Sales Rep',
  userId = 0,
}: Props) {
  const [transitionOpen, setTransitionOpen] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const { data: activityData, isLoading: logLoading } = useActivityLog(contract.ref_id)
  const { updateMutation } = useMutateContract()

  const isEditable = (EDITABLE_STATUSES as readonly string[]).includes(contract.status)
  const canEdit =
    userRole === 'Admin' || userRole === 'Manager' || contract.owner_id === userId

  return (
    <Box>
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
        <Typography variant="h5" component="h1">
          {contract.ref_id}
        </Typography>
        <ContractStatusChip status={contract.status} size="medium" />
        <Box sx={{ flex: 1 }} />
        {isEditable && canEdit && !editMode && (
          <Button variant="outlined" onClick={() => setEditMode(true)}>
            Edit
          </Button>
        )}
        <Button
          variant="contained"
          onClick={() => setTransitionOpen(true)}
          aria-label="Change contract status"
        >
          Change Status
        </Button>
      </Stack>

      {updateMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {(updateMutation.error as Error).message}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" color="text.secondary">
            Value
          </Typography>
          <Typography variant="body1">
            ${Number(contract.value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </Typography>
        </Grid>
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" color="text.secondary">
            Account
          </Typography>
          <Typography variant="body1">{contract.account_id}</Typography>
        </Grid>
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" color="text.secondary">
            Period
          </Typography>
          <Typography variant="body1">
            {contract.start_date} — {contract.end_date}
          </Typography>
        </Grid>
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" color="text.secondary">
            Owner
          </Typography>
          <Typography variant="body1">{contract.owner_id}</Typography>
        </Grid>
        {contract.description && (
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="text.secondary">
              Description
            </Typography>
            <Typography variant="body1">{contract.description}</Typography>
          </Grid>
        )}
      </Grid>

      <Divider sx={{ my: 3 }} />

      <ContractAttachmentPanel
        refId={contract.ref_id}
        attachment={contract.attachment}
        canEdit={canEdit}
      />

      <Divider sx={{ my: 3 }} />

      <Typography variant="h6" gutterBottom>
        Activity Log
      </Typography>
      {logLoading ? (
        <CircularProgress size={24} aria-label="Loading activity log" />
      ) : (
        <ContractActivityLog logs={activityData?.logs ?? []} />
      )}

      <ContractTransitionDialog
        open={transitionOpen}
        onClose={() => setTransitionOpen(false)}
        contract={contract}
        userRole={userRole}
      />
    </Box>
  )
}
