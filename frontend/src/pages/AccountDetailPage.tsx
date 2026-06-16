import { useState } from 'react';
import { useParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogActions from '@mui/material/DialogActions';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import MuiLink from '@mui/material/Link';
import { useAuth } from '../hooks/useAuth';
import { useAccount, useAccountTimeline, useArchiveAccount } from '../hooks/useAccounts';
import AccountTimeline from '../components/contacts/AccountTimeline';

export default function AccountDetailPage() {
  const { id } = useParams<{ id: string }>();
  const accountId = Number(id);
  const { user } = useAuth();
  const isAdmin = user?.role === 'Admin';
  const { data: account, isLoading } = useAccount(accountId);
  const { data: timeline, isLoading: timelineLoading } = useAccountTimeline(accountId);
  const archive = useArchiveAccount();
  const [archiveOpen, setArchiveOpen] = useState(false);

  if (isLoading) return <CircularProgress sx={{ m: 4 }} />;
  if (!account) return <Typography sx={{ m: 4 }}>Account not found.</Typography>;

  return (
    <Box sx={{ p: 3, maxWidth: 800 }}>
      <Card>
        <CardHeader
          title={account.name}
          subheader={
            <Stack direction="row" spacing={2} flexWrap="wrap">
              {account.industry && <Typography variant="body2">{account.industry}</Typography>}
              {account.company_size && (
                <Typography variant="body2" color="text.secondary">
                  · {account.company_size}
                </Typography>
              )}
              {account.website && (
                <MuiLink href={account.website} target="_blank" rel="noreferrer" variant="body2">
                  Website
                </MuiLink>
              )}
            </Stack>
          }
          action={
            isAdmin && !account.is_archived ? (
              <Button size="small" color="error" onClick={() => setArchiveOpen(true)}>
                Archive
              </Button>
            ) : null
          }
        />
        <CardContent>
          {account.billing_address && (
            <Typography variant="body2" gutterBottom>
              Address: {account.billing_address}
            </Typography>
          )}
          <Typography variant="body2" gutterBottom>
            Contacts: <strong>{account.contact_count}</strong>
          </Typography>

          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle1" gutterBottom>
            Activity Timeline
          </Typography>
          <AccountTimeline items={timeline} isLoading={timelineLoading} />
        </CardContent>
      </Card>

      <Dialog open={archiveOpen} onClose={() => setArchiveOpen(false)}>
        <DialogTitle>Archive account?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setArchiveOpen(false)}>Cancel</Button>
          <Button
            color="error"
            onClick={() => {
              archive.mutate(accountId);
              setArchiveOpen(false);
            }}
          >
            Archive
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
