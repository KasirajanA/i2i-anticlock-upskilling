import { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import CircularProgress from '@mui/material/CircularProgress';
import ArchiveIcon from '@mui/icons-material/Archive';
import { Link as RouterLink } from 'react-router-dom';
import MuiLink from '@mui/material/Link';
import { useAuth } from '../hooks/useAuth';
import { useAccountList, useArchiveAccount, useCreateAccount } from '../hooks/useAccounts';
import TextField2 from '@mui/material/TextField';
import Button2 from '@mui/material/Button';

function AccountCreateForm({ onSuccess }: { onSuccess: () => void }) {
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const create = useCreateAccount();
  return (
    <Stack component="form" spacing={2} sx={{ p: 2 }}
      onSubmit={async (e) => {
        e.preventDefault();
        await create.mutateAsync({ name, industry: industry || undefined });
        onSuccess();
      }}
    >
      <TextField2 label="Company name" value={name} onChange={(e) => setName(e.target.value)} required />
      <TextField2 label="Industry" value={industry} onChange={(e) => setIndustry(e.target.value)} />
      <Button2 type="submit" variant="contained" disabled={create.isPending}>Save account</Button2>
    </Stack>
  );
}

export default function AccountListPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'Admin';
  const canWrite = user?.role !== 'Support Agent';

  const [q, setQ] = useState('');
  const [includeArchived, setIncludeArchived] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const { data, isLoading } = useAccountList({ q, include_archived: includeArchived });
  const archive = useArchiveAccount();

  const accounts = data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Accounts</Typography>
        {canWrite && (
          <Button variant="contained" onClick={() => setDrawerOpen(true)}>
            New Account
          </Button>
        )}
      </Stack>

      <Stack direction="row" spacing={2} mb={2} alignItems="center">
        <TextField
          size="small"
          placeholder="Search accounts…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          sx={{ width: 260 }}
        />
        <FormControlLabel
          control={
            <Switch
              checked={includeArchived}
              onChange={(e) => setIncludeArchived(e.target.checked)}
              size="small"
            />
          }
          label="Show archived"
        />
      </Stack>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Industry</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Status</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            )}
            {accounts.map((a) => (
              <TableRow key={a.id} hover>
                <TableCell>
                  <MuiLink component={RouterLink} to={`/accounts/${a.id}`} underline="hover">
                    {a.name}
                  </MuiLink>
                </TableCell>
                <TableCell>{a.industry ?? '—'}</TableCell>
                <TableCell>{a.company_size ?? '—'}</TableCell>
                <TableCell>{a.is_archived ? 'Archived' : 'Active'}</TableCell>
                <TableCell align="right">
                  {isAdmin && !a.is_archived && (
                    <IconButton size="small" onClick={() => archive.mutate(a.id)}>
                      <ArchiveIcon fontSize="small" />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && accounts.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">No accounts found.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)} PaperProps={{ sx: { width: 380 } }}>
        <AccountCreateForm onSuccess={() => setDrawerOpen(false)} />
      </Drawer>
    </Box>
  );
}
