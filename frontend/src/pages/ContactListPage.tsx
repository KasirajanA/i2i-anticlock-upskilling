import { useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import IconButton from '@mui/material/IconButton';
import Collapse from '@mui/material/Collapse';
import CircularProgress from '@mui/material/CircularProgress';
import FilterListIcon from '@mui/icons-material/FilterList';
import BookmarksIcon from '@mui/icons-material/Bookmarks';
import { useAuth } from '../hooks/useAuth';
import { useContactList, useArchiveContact } from '../hooks/useContacts';
import ContactRow from '../components/contacts/ContactRow';
import ContactForm from '../components/contacts/ContactForm';
import CSVImportDialog from '../components/contacts/CSVImportDialog';
import FilterBuilder from '../components/contacts/FilterBuilder';
import SegmentPanel from '../components/contacts/SegmentPanel';
import type { FilterSpec } from '../types/contact';

const EMPTY_SPEC: FilterSpec = { conditions: [] };

export default function ContactListPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'Admin';
  const canWrite = user?.role !== 'Support Agent';

  const [q, setQ] = useState('');
  const [filterSpec, setFilterSpec] = useState<FilterSpec>(EMPTY_SPEC);
  const [showFilters, setShowFilters] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [segmentOpen, setSegmentOpen] = useState(false);

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } = useContactList({ q });
  const archive = useArchiveContact();

  const contacts = data?.pages.flatMap((p) => p.items) ?? [];

  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const el = e.currentTarget;
      if (el.scrollHeight - el.scrollTop - el.clientHeight < 100 && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage],
  );

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Contacts</Typography>
        <Stack direction="row" spacing={1}>
          <IconButton onClick={() => setSegmentOpen(true)} title="Segments">
            <BookmarksIcon />
          </IconButton>
          {canWrite && (
            <>
              <Button variant="outlined" onClick={() => setImportOpen(true)}>
                Import
              </Button>
              <Button variant="contained" onClick={() => setDrawerOpen(true)}>
                New Contact
              </Button>
            </>
          )}
        </Stack>
      </Stack>

      <Stack direction="row" spacing={1} mb={1} alignItems="center">
        <TextField
          size="small"
          placeholder="Search contacts…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          sx={{ width: 280 }}
        />
        <Button
          size="small"
          startIcon={<FilterListIcon />}
          onClick={() => setShowFilters((v) => !v)}
        >
          Advanced filters
        </Button>
      </Stack>

      <Collapse in={showFilters}>
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <FilterBuilder value={filterSpec} onChange={setFilterSpec} />
        </Paper>
      </Collapse>

      <TableContainer
        component={Paper}
        sx={{ maxHeight: 600, overflow: 'auto' }}
        onScroll={handleScroll}
      >
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Account</TableCell>
              <TableCell>Tags</TableCell>
              <TableCell>Owner</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            )}
            {contacts.map((c) => (
              <ContactRow
                key={c.id}
                contact={c}
                isAdmin={isAdmin}
                onArchive={(id) => archive.mutate(id)}
              />
            ))}
            {!isLoading && contacts.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No contacts found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {isFetchingNextPage && (
        <Box textAlign="center" mt={1}>
          <CircularProgress size={20} />
        </Box>
      )}

      <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)} PaperProps={{ sx: { width: 420 } }}>
        <ContactForm onSuccess={() => setDrawerOpen(false)} />
      </Drawer>

      <CSVImportDialog open={importOpen} onClose={() => setImportOpen(false)} />

      <SegmentPanel
        open={segmentOpen}
        onClose={() => setSegmentOpen(false)}
        activeFilters={filterSpec}
        onApplySegment={(spec) => {
          setFilterSpec(spec);
          setSegmentOpen(false);
        }}
      />
    </Box>
  );
}
