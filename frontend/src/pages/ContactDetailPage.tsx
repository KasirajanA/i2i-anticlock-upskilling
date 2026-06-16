import { useState } from 'react';
import { useParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Chip from '@mui/material/Chip';
import Drawer from '@mui/material/Drawer';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogActions from '@mui/material/DialogActions';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import CircularProgress from '@mui/material/CircularProgress';
import { Link as RouterLink } from 'react-router-dom';
import MuiLink from '@mui/material/Link';
import { useAuth } from '../hooks/useAuth';
import { useContact, useArchiveContact } from '../hooks/useContacts';
import ContactForm from '../components/contacts/ContactForm';
import CustomFieldForm from '../components/contacts/CustomFieldForm';

export default function ContactDetailPage() {
  const { id } = useParams<{ id: string }>();
  const contactId = Number(id);
  const { user } = useAuth();
  const isAdmin = user?.role === 'Admin';
  const { data: contact, isLoading } = useContact(contactId);
  const archive = useArchiveContact();
  const [editOpen, setEditOpen] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);

  if (isLoading) return <CircularProgress sx={{ m: 4 }} />;
  if (!contact) return <Typography sx={{ m: 4 }}>Contact not found.</Typography>;

  return (
    <Box sx={{ p: 3, maxWidth: 800 }}>
      <Card>
        <CardHeader
          title={`${contact.first_name} ${contact.last_name}`}
          subheader={
            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
              <Typography variant="body2">{contact.email}</Typography>
              {contact.job_title && (
                <Typography variant="body2" color="text.secondary">
                  · {contact.job_title}
                </Typography>
              )}
            </Stack>
          }
          action={
            <Stack direction="row" spacing={1}>
              <Button size="small" onClick={() => setEditOpen(true)}>
                Edit
              </Button>
              {isAdmin && (
                <Button size="small" color="error" onClick={() => setArchiveOpen(true)}>
                  Archive
                </Button>
              )}
            </Stack>
          }
        />
        <CardContent>
          {contact.accounts?.length > 0 && (
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>
                Accounts
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {contact.accounts.map((a) => (
                  <Chip
                    key={a.id}
                    component={RouterLink}
                    to={`/accounts/${a.id}`}
                    clickable
                    label={a.is_archived ? `${a.name} (archived)` : a.name}
                    variant={a.is_archived ? 'outlined' : 'filled'}
                  />
                ))}
              </Stack>
            </Box>
          )}

          {contact.phone && (
            <Typography variant="body2" gutterBottom>
              Phone: <MuiLink href={`tel:${contact.phone}`}>{contact.phone}</MuiLink>
            </Typography>
          )}

          {contact.tags?.length > 0 && (
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>Tags</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {contact.tags.map((t) => <Chip key={t} label={t} size="small" />)}
              </Stack>
            </Box>
          )}

          {contact.custom_fields?.length > 0 && (
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>Custom Fields</Typography>
              <Table size="small">
                <TableBody>
                  {contact.custom_fields.map((cf) => (
                    <TableRow key={cf.key}>
                      <TableCell sx={{ fontWeight: 500 }}>{cf.label}</TableCell>
                      <TableCell>{cf.value ?? '—'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
        </CardContent>
      </Card>

      {isAdmin && <CustomFieldForm entityType="contact" />}

      <Drawer anchor="right" open={editOpen} onClose={() => setEditOpen(false)} PaperProps={{ sx: { width: 420 } }}>
        <ContactForm onSuccess={() => setEditOpen(false)} />
      </Drawer>

      <Dialog open={archiveOpen} onClose={() => setArchiveOpen(false)}>
        <DialogTitle>Archive contact?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setArchiveOpen(false)}>Cancel</Button>
          <Button
            color="error"
            onClick={() => {
              archive.mutate(contactId);
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
