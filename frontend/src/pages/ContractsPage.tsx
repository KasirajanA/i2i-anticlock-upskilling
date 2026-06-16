import AddIcon from '@mui/icons-material/Add'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import Dialog from '@mui/material/Dialog'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import Typography from '@mui/material/Typography'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ContractForm from '../components/contracts/ContractForm'
import ContractList from '../components/contracts/ContractList'
import { useMutateContract } from '../hooks/useContracts'
import type { ContractCreateRequest } from '../types/contracts'

export default function ContractsPage() {
  const [createOpen, setCreateOpen] = useState(false)
  const navigate = useNavigate()
  const { createMutation } = useMutateContract()

  function handleCreate(data: ContractCreateRequest) {
    createMutation.mutate(data, {
      onSuccess: (contract) => {
        setCreateOpen(false)
        navigate(`/contracts/${contract.ref_id}`)
      },
    })
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ flex: 1 }}>
          Contracts
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          aria-label="Create new contract"
        >
          New Contract
        </Button>
      </Box>

      <ContractList />

      <Dialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        maxWidth="sm"
        fullWidth
        aria-labelledby="create-contract-dialog-title"
      >
        <DialogTitle id="create-contract-dialog-title">New Contract</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <ContractForm
              mode="create"
              onSubmit={(data) => handleCreate(data as ContractCreateRequest)}
              isLoading={createMutation.isPending}
              error={
                createMutation.isError
                  ? (createMutation.error as Error).message
                  : null
              }
            />
          </Box>
        </DialogContent>
      </Dialog>
    </Container>
  )
}
