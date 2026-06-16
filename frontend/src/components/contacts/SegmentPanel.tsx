import { useState } from 'react';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import { useCreateSegment, useSegmentList } from '../../hooks/useSegments';
import type { FilterSpec } from '../../types/contact';

interface Props {
  open: boolean;
  onClose: () => void;
  onApplySegment: (spec: FilterSpec) => void;
  activeFilters: FilterSpec;
}

export default function SegmentPanel({ open, onClose, onApplySegment, activeFilters }: Props) {
  const { data: segments = [] } = useSegmentList('contact');
  const createSegment = useCreateSegment('contact');
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [segmentName, setSegmentName] = useState('');

  const handleSave = async () => {
    if (!segmentName.trim()) return;
    await createSegment.mutateAsync({
      name: segmentName.trim(),
      entity_type: 'contact',
      filter_spec: activeFilters,
    });
    setSegmentName('');
    setSaveDialogOpen(false);
  };

  return (
    <>
      <Drawer anchor="right" open={open} onClose={onClose} PaperProps={{ sx: { width: 320 } }}>
        <Stack sx={{ p: 2 }} spacing={2}>
          <Typography variant="h6">Saved Segments</Typography>
          <Button
            variant="outlined"
            size="small"
            onClick={() => setSaveDialogOpen(true)}
            disabled={activeFilters.conditions.length === 0}
          >
            Save active filters as segment
          </Button>
          <List dense>
            {segments.map((seg) => (
              <ListItem
                key={seg.id}
                secondaryAction={
                  <Button size="small" onClick={() => onApplySegment(seg.filter_spec)}>
                    Apply
                  </Button>
                }
              >
                <ListItemText
                  primary={seg.name}
                  secondary={<Chip label={`${seg.live_count} contacts`} size="small" />}
                />
              </ListItem>
            ))}
            {segments.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
                No segments saved yet.
              </Typography>
            )}
          </List>
        </Stack>
      </Drawer>
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Save as Segment</DialogTitle>
        <DialogContent>
          <TextField
            label="Segment name"
            value={segmentName}
            onChange={(e) => setSegmentName(e.target.value)}
            fullWidth
            autoFocus
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" disabled={!segmentName.trim()}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
