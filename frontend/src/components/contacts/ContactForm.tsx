import { useState } from 'react';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Autocomplete from '@mui/material/Autocomplete';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import { useCreateContact } from '../../hooks/useContacts';
import { useAccountList } from '../../hooks/useAccounts';
import DuplicateWarningBanner from './DuplicateWarningBanner';
import type { DuplicateWarning } from '../../types/contact';

interface Props {
  onSuccess: () => void;
}

export default function ContactForm({ onSuccess }: Props) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [accountIds, setAccountIds] = useState<number[]>([]);
  const [duplicateWarning, setDuplicateWarning] = useState<DuplicateWarning | null>(null);

  const create = useCreateContact();
  const { data: accountPages } = useAccountList({});
  const accounts = accountPages?.pages.flatMap((p) => p.items) ?? [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await create.mutateAsync({
      first_name: firstName,
      last_name: lastName,
      email,
      phone: phone || undefined,
      job_title: jobTitle || undefined,
      account_ids: accountIds,
      tags,
    });
    if (result.duplicate_warning) {
      setDuplicateWarning(result.duplicate_warning);
    } else {
      onSuccess();
    }
  };

  return (
    <Stack component="form" onSubmit={handleSubmit} spacing={2} sx={{ p: 2 }}>
      {duplicateWarning && (
        <DuplicateWarningBanner
          warning={duplicateWarning}
          onClose={() => setDuplicateWarning(null)}
        />
      )}
      <Stack direction="row" spacing={2}>
        <TextField
          label="First name"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
          fullWidth
        />
        <TextField
          label="Last name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          required
          fullWidth
        />
      </Stack>
      <TextField
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        fullWidth
      />
      <TextField
        label="Phone"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        fullWidth
      />
      <TextField
        label="Job title"
        value={jobTitle}
        onChange={(e) => setJobTitle(e.target.value)}
        fullWidth
      />
      <Autocomplete
        multiple
        freeSolo
        options={[]}
        value={tags}
        onChange={(_, v) => setTags(v as string[])}
        renderTags={(value, getTagProps) =>
          value.map((option, index) => (
            <Chip label={option} size="small" {...getTagProps({ index })} key={option} />
          ))
        }
        renderInput={(params) => <TextField {...params} label="Tags" placeholder="Add tag" />}
      />
      <Autocomplete
        multiple
        options={accounts}
        getOptionLabel={(o) => o.name}
        onChange={(_, v) => setAccountIds(v.map((a) => a.id))}
        renderInput={(params) => <TextField {...params} label="Accounts" />}
      />
      <Button
        type="submit"
        variant="contained"
        disabled={create.isPending}
        startIcon={create.isPending ? <CircularProgress size={16} /> : null}
      >
        Save contact
      </Button>
    </Stack>
  );
}
