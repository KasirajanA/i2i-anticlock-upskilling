import CssBaseline from '@mui/material/CssBaseline'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import ContractDetailPage from './pages/ContractDetailPage'
import ContractsPage from './pages/ContractsPage'
import AccessDeniedPage from './pages/AccessDeniedPage'
import LoginPage from './pages/LoginPage'
import UserListPage from './pages/UserListPage'
import ProfilePage from './pages/ProfilePage'
import TeamListPage from './pages/TeamListPage'
import ContactListPage from './pages/ContactListPage'
import ContactDetailPage from './pages/ContactDetailPage'
import AccountListPage from './pages/AccountListPage'
import AccountDetailPage from './pages/AccountDetailPage'
import LeadListPage from './pages/LeadListPage'
import LeadDetailPage from './pages/LeadDetailPage'
import { AuthProvider } from './context/AuthContext'
import SessionGuard from './components/auth/SessionGuard'
import RequireRole from './components/auth/RequireRole'

const theme = createTheme()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/access-denied" element={<AccessDeniedPage />} />
              <Route
                path="/contracts"
                element={<SessionGuard><ContractsPage /></SessionGuard>}
              />
              <Route
                path="/contracts/:refId"
                element={<SessionGuard><ContractDetailPage /></SessionGuard>}
              />
              <Route
                path="/users"
                element={
                  <SessionGuard>
                    <RequireRole allowedRoles={['Admin']}>
                      <UserListPage />
                    </RequireRole>
                  </SessionGuard>
                }
              />
              <Route
                path="/teams"
                element={
                  <SessionGuard>
                    <RequireRole allowedRoles={['Admin']}>
                      <TeamListPage />
                    </RequireRole>
                  </SessionGuard>
                }
              />
              <Route
                path="/profile"
                element={<SessionGuard><ProfilePage /></SessionGuard>}
              />
              <Route
                path="/contacts"
                element={<SessionGuard><ContactListPage /></SessionGuard>}
              />
              <Route
                path="/contacts/:id"
                element={<SessionGuard><ContactDetailPage /></SessionGuard>}
              />
              <Route
                path="/accounts"
                element={<SessionGuard><AccountListPage /></SessionGuard>}
              />
              <Route
                path="/accounts/:id"
                element={<SessionGuard><AccountDetailPage /></SessionGuard>}
              />
              <Route
                path="/leads"
                element={
                  <SessionGuard>
                    <RequireRole allowedRoles={['Admin', 'Manager', 'Sales Rep']}>
                      <LeadListPage />
                    </RequireRole>
                  </SessionGuard>
                }
              />
              <Route
                path="/leads/:id"
                element={
                  <SessionGuard>
                    <RequireRole allowedRoles={['Admin', 'Manager', 'Sales Rep']}>
                      <LeadDetailPage />
                    </RequireRole>
                  </SessionGuard>
                }
              />
              <Route path="/" element={<SessionGuard><ContractsPage /></SessionGuard>} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
