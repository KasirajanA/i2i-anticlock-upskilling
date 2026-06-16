import Stack from '@mui/material/Stack';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import type { FilterCondition, FilterSpec } from '../../types/contact';

const FIELDS = [
  { value: 'name', label: 'Name' },
  { value: 'email', label: 'Email' },
  { value: 'tag', label: 'Tag' },
  { value: 'account_id', label: 'Account' },
];

const OPERATORS = [
  { value: 'eq', label: 'is' },
  { value: 'contains', label: 'contains' },
  { value: 'in', label: 'includes' },
];

interface Props {
  value: FilterSpec;
  onChange: (spec: FilterSpec) => void;
}

export default function FilterBuilder({ value, onChange }: Props) {
  const conditions = value.conditions;

  const update = (idx: number, patch: Partial<FilterCondition>) => {
    const next = conditions.map((c, i) => (i === idx ? { ...c, ...patch } : c));
    onChange({ conditions: next });
  };

  const remove = (idx: number) => {
    onChange({ conditions: conditions.filter((_, i) => i !== idx) });
  };

  const add = () => {
    if (conditions.length >= 5) return;
    onChange({ conditions: [...conditions, { field: 'name', operator: 'contains', value: '' }] });
  };

  return (
    <Stack spacing={1}>
      {conditions.map((cond, idx) => (
        <Stack key={idx} direction="row" spacing={1} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Field</InputLabel>
            <Select
              value={cond.field}
              label="Field"
              onChange={(e) => update(idx, { field: e.target.value })}
            >
              {FIELDS.map((f) => (
                <MenuItem key={f.value} value={f.value}>{f.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 110 }}>
            <InputLabel>Operator</InputLabel>
            <Select
              value={cond.operator}
              label="Operator"
              onChange={(e) => update(idx, { operator: e.target.value as FilterCondition['operator'] })}
            >
              {OPERATORS.map((o) => (
                <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            size="small"
            label="Value"
            value={cond.value}
            onChange={(e) => update(idx, { value: e.target.value })}
            sx={{ flex: 1 }}
          />
          <IconButton size="small" onClick={() => remove(idx)}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      ))}
      <Button
        startIcon={<AddIcon />}
        onClick={add}
        disabled={conditions.length >= 5}
        size="small"
        variant="outlined"
        sx={{ alignSelf: 'flex-start' }}
      >
        Add filter
      </Button>
    </Stack>
  );
}
