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
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import CircularProgress from '@mui/material/CircularProgress';
import { Link as RouterLink } from 'react-router-dom';
import MuiLink from '@mui/material/Link';
import { useAuth } from '../hooks/useAuth';
import { useLeadList, useCreateLead, useUpdateLead } from '../hooks/useLeads';
import LeadStatusChip from '../components/contacts/LeadStatusChip';
import LeadConvertDialog from '../components/contacts/LeadConvertDialog';
import type { LeadStatus } from '../types/contact';

function LeadCreateForm({ onSuccess }: { onSuccess: () => void }) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [notes, setNotes] = useState('');
  const create = useCreateLead();
  return (
    <Stack component="form" spacing={2} sx={{ p: 2 }}
      onSubmit={async (e) => {
        e.preventDefault();
        await create.mutateAsync({ first_name: firstName, last_name: lastName, email, company_name: company || undefined, notes: notes || undefined });
        onSuccess();
      }}
    >
      <Stack direction="row" spacing={2}>
        <TextField label="First name" value={firstName} onChange={(e) => setFirstName(e.target.value)} required fullWidth />
        <TextField label="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} required fullWidth />
      </Stack>
      <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <TextField label="Company" value={company} onChange={(e) => setCompany(e.target.value)} />
      <TextField label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} multiline rows={3} />
      <Button type="submit" variant="contained" disabled={create.isPending}>Save lead</Button>
    </Stack>
  );
}

export default function LeadListPage() {
  const { user } = useAuth();
  const canWrite = user?.role === 'Admin' || user?.role === 'Sales Rep';

  const [statusFilter, setStatusFilter] = useState<LeadStatus | ''>('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [convertId, setConvertId] = useState<number | null>(null);

  const { data, isLoading } = useLeadList(statusFilter ? { status: statusFilter } : {});
  const updateLead = useUpdateLead();

  const leads = data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Leads</Typography>
        {canWrite && (
          <Button variant="contained" onClick={() => setDrawerOpen(true)}>
            New Lead
          </Button>
        )}
      </Stack>

      <ToggleButtonGroup
        value={statusFilter}
        exclusive
        onChange={(_, v) => setStatusFilter(v ?? '')}
        size="small"
        sx={{ mb: 2 }}
      >
        {(['', 'new', 'contacted', 'qualified', 'converted', 'disqualified'] as const).map((s) => (
          <ToggleButton key={s} value={s}>
            {s || 'All'}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Status</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={5} align="center"><CircularProgress size={24} /></TableCell>
              </TableRow>
            )}
            {leads.map((lead) => (
              <TableRow key={lead.id} hover>
                <TableCell>
                  <MuiLink component={RouterLink} to={`/leads/${lead.id}`} underline="hover">
                    {lead.first_name} {lead.last_name}
                  </MuiLink>
                </TableCell>
                <TableCell>{lead.email}</TableCell>
                <TableCell>{lead.company_name ?? '—'}</TableCell>
                <TableCell><LeadStatusChip status={lead.status} /></TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    {canWrite && lead.status === 'qualified' && (
                      <Button size="small" onClick={() => setConvertId(lead.id)}>
                        Convert
                      </Button>
                    )}
                    {canWrite && lead.status === 'new' && (
                      <Button size="small" onClick={() => updateLead.mutate({ id: lead.id, body: { status: 'contacted' } })}>
                        Contact
                      </Button>
                    )}
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && leads.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">No leads found.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)} PaperProps={{ sx: { width: 400 } }}>
        <LeadCreateForm onSuccess={() => setDrawerOpen(false)} />
      </Drawer>

      {convertId !== null && (
        <LeadConvertDialog
          leadId={convertId}
          open={convertId !== null}
          onClose={() => setConvertId(null)}
        />
      )}
    </Box>
  );
}
