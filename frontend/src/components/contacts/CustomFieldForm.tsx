import { useState } from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Fab from '@mui/material/Fab';
import AddIcon from '@mui/icons-material/Add';
import Alert from '@mui/material/Alert';
import { useMutation, useQueryClient } from '@tanstack/react-query';

function toSnakeCase(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '');
}

async function createCustomField(body: {
  entity_type: string;
  field_key: string;
  label: string;
  field_type: string;
  options?: string[];
  required: boolean;
}): Promise<void> {
  const resp = await fetch('/api/v1/custom-fields', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const d = await resp.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(d.detail ?? 'Request failed');
  }
}

interface Props {
  entityType: string;
}

export default function CustomFieldForm({ entityType }: Props) {
  const [open, setOpen] = useState(false);
  const [label, setLabel] = useState('');
  const [fieldType, setFieldType] = useState('text');
  const [required, setRequired] = useState(false);
  const [optionInput, setOptionInput] = useState('');
  const [options, setOptions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: createCustomField,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['custom-fields', entityType] });
      setOpen(false);
      resetForm();
    },
    onError: (e: Error) => setError(e.message),
  });

  const resetForm = () => {
    setLabel('');
    setFieldType('text');
    setRequired(false);
    setOptions([]);
    setOptionInput('');
    setError(null);
  };

  const handleSave = () => {
    mutation.mutate({
      entity_type: entityType,
      field_key: toSnakeCase(label),
      label,
      field_type: fieldType,
      options: fieldType === 'select' ? options : undefined,
      required,
    });
  };

  const addOption = () => {
    const trimmed = optionInput.trim();
    if (trimmed && !options.includes(trimmed)) {
      setOptions((prev) => [...prev, trimmed]);
    }
    setOptionInput('');
  };

  return (
    <>
      <Fab
        size="small"
        color="primary"
        onClick={() => setOpen(true)}
        title="Add Custom Field"
        sx={{ position: 'absolute', bottom: 16, right: 16 }}
      >
        <AddIcon />
      </Fab>

      <Dialog open={open} onClose={() => { setOpen(false); resetForm(); }} maxWidth="xs" fullWidth>
        <DialogTitle>Add Custom Field</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              label="Label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              helperText={label ? `Key: ${toSnakeCase(label)}` : ''}
              required
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Field type</InputLabel>
              <Select value={fieldType} label="Field type" onChange={(e) => setFieldType(e.target.value)}>
                {['text', 'number', 'date', 'boolean', 'select'].map((t) => (
                  <MenuItem key={t} value={t}>{t}</MenuItem>
                ))}
              </Select>
            </FormControl>
            {fieldType === 'select' && (
              <Stack spacing={1}>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {options.map((o) => (
                    <Chip
                      key={o}
                      label={o}
                      size="small"
                      onDelete={() => setOptions((prev) => prev.filter((x) => x !== o))}
                    />
                  ))}
                </Stack>
                <Stack direction="row" spacing={1}>
                  <TextField
                    size="small"
                    label="Add option"
                    value={optionInput}
                    onChange={(e) => setOptionInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addOption()}
                    fullWidth
                  />
                  <Button onClick={addOption} variant="outlined" size="small">Add</Button>
                </Stack>
              </Stack>
            )}
            <FormControlLabel
              control={<Checkbox checked={required} onChange={(e) => setRequired(e.target.checked)} />}
              label="Required"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setOpen(false); resetForm(); }}>Cancel</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={!label.trim() || mutation.isPending || (fieldType === 'select' && options.length === 0)}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
