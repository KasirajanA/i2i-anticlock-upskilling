import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import { Link } from 'react-router-dom'

export default function AccessDeniedPage() {
  return (
    <Box sx={{ p: 4, textAlign: 'center' }}>
      <Typography variant="h4" mb={2}>Access Denied</Typography>
      <Typography color="text.secondary" mb={3}>
        You do not have permission to view this page.
      </Typography>
      <Button component={Link} to="/dashboard" variant="contained">
        Go to Dashboard
      </Button>
    </Box>
  )
}
