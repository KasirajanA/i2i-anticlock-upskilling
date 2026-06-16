import { useState } from 'react';
import { useParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Button from '@mui/material/Button';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import CircularProgress from '@mui/material/CircularProgress';
import { Link as RouterLink } from 'react-router-dom';
import MuiLink from '@mui/material/Link';
import { useAuth } from '../hooks/useAuth';
import { useLead } from '../hooks/useLeads';
import LeadStatusChip from '../components/contacts/LeadStatusChip';
import LeadConvertDialog from '../components/contacts/LeadConvertDialog';
import type { LeadStatus } from '../types/contact';

const STATUS_STEPS: LeadStatus[] = ['new', 'contacted', 'qualified', 'converted'];

function activeStep(status: LeadStatus) {
  const idx = STATUS_STEPS.indexOf(status);
  return idx >= 0 ? idx : 0;
}

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const leadId = Number(id);
  const { user } = useAuth();
  const canWrite = user?.role === 'Admin' || user?.role === 'Sales Rep';
  const { data: lead, isLoading } = useLead(leadId);
  const [convertOpen, setConvertOpen] = useState(false);

  if (isLoading) return <CircularProgress sx={{ m: 4 }} />;
  if (!lead) return <Typography sx={{ m: 4 }}>Lead not found.</Typography>;

  return (
    <Box sx={{ p: 3, maxWidth: 700 }}>
      <Card>
        <CardHeader
          title={`${lead.first_name} ${lead.last_name}`}
          subheader={lead.email}
          action={<LeadStatusChip status={lead.status} />}
        />
        <CardContent>
          {lead.company_name && (
            <Typography variant="body2" gutterBottom>Company: {lead.company_name}</Typography>
          )}

          {lead.status !== 'disqualified' && (
            <Box mb={3}>
              <Stepper activeStep={activeStep(lead.status)} sx={{ mb: 2 }}>
                {STATUS_STEPS.map((s) => (
                  <Step key={s}><StepLabel>{s}</StepLabel></Step>
                ))}
              </Stepper>
            </Box>
          )}

          {lead.status === 'disqualified' && lead.disqualify_reason && (
            <Typography variant="body2" color="error" gutterBottom>
              Disqualified: {lead.disqualify_reason}
            </Typography>
          )}

          {lead.notes && (
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>
              {lead.notes}
            </Typography>
          )}

          {lead.converted_contact_id && (
            <Typography variant="body2">
              Converted contact:{' '}
              <MuiLink component={RouterLink} to={`/contacts/${lead.converted_contact_id}`}>
                #{lead.converted_contact_id}
              </MuiLink>
            </Typography>
          )}

          {canWrite && lead.status === 'qualified' && (
            <Stack direction="row" spacing={1} mt={2}>
              <Button variant="contained" onClick={() => setConvertOpen(true)}>
                Convert Lead
              </Button>
            </Stack>
          )}
        </CardContent>
      </Card>

      <LeadConvertDialog
        leadId={leadId}
        open={convertOpen}
        onClose={() => setConvertOpen(false)}
      />
    </Box>
  );
}
