import { useRef, useState } from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import FormControlLabel from '@mui/material/FormControlLabel';
import RadioGroup from '@mui/material/RadioGroup';
import Radio from '@mui/material/Radio';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Stack from '@mui/material/Stack';
import { importContacts } from '../../services/contactApi';
import type { ImportResult } from '../../types/contact';

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function CSVImportDialog({ open, onClose }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<'skip' | 'overwrite'>('skip');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const res = await importContacts(file, mode);
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setResult(null);
    setLoading(false);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Import Contacts from CSV</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            style={{ display: 'none' }}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <Button variant="outlined" onClick={() => fileRef.current?.click()}>
            {file ? file.name : 'Choose CSV file'}
          </Button>
          <RadioGroup value={mode} onChange={(e) => setMode(e.target.value as 'skip' | 'overwrite')}>
            <FormControlLabel value="skip" control={<Radio />} label="Skip duplicates (default)" />
            <FormControlLabel value="overwrite" control={<Radio />} label="Overwrite existing" />
          </RadioGroup>
          {loading && <LinearProgress />}
          {result && (
            <>
              <Typography variant="body2">
                Imported: <strong>{result.imported}</strong> &nbsp; Skipped:{' '}
                <strong>{result.skipped}</strong> &nbsp; Errors:{' '}
                <strong>{result.errors}</strong>
              </Typography>
              {result.error_details.length > 0 && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="body2">Show errors ({result.error_details.length})</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {result.error_details.map((e, i) => (
                      <Typography key={i} variant="caption" display="block">
                        Row {e.row}: {e.reason}
                      </Typography>
                    ))}
                  </AccordionDetails>
                </Accordion>
              )}
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        {!result && (
          <Button onClick={handleUpload} variant="contained" disabled={!file || loading}>
            Upload
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
