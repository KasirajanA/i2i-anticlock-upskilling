import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Breadcrumbs from '@mui/material/Breadcrumbs'
import CircularProgress from '@mui/material/CircularProgress'
import Container from '@mui/material/Container'
import Link from '@mui/material/Link'
import Typography from '@mui/material/Typography'
import { Link as RouterLink, useParams } from 'react-router-dom'
import ContractDetail from '../components/contracts/ContractDetail'
import { useContract } from '../hooks/useContracts'

export default function ContractDetailPage() {
  const { refId } = useParams<{ refId: string }>()
  const { data: contract, isLoading, isError, error } = useContract(refId ?? '')

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/contracts" underline="hover" color="inherit">
          Contracts
        </Link>
        <Typography color="text.primary">{refId}</Typography>
      </Breadcrumbs>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress aria-label="Loading contract" />
        </Box>
      )}

      {isError && (
        <Alert severity="error">{(error as Error).message}</Alert>
      )}

      {contract && (
        <ContractDetail contract={contract} />
      )}
    </Container>
  )
}
