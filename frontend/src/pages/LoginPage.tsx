import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Typography from '@mui/material/Typography'
import LoginForm from '../components/auth/LoginForm'

export default function LoginPage() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
      <Card sx={{ maxWidth: 420, width: '100%', mx: 2 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h5" mb={2} textAlign="center">
            Sign In
          </Typography>
          <LoginForm />
        </CardContent>
      </Card>
    </Box>
  )
}
