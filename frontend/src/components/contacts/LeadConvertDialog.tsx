import { useState } from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import CircularProgress from '@mui/material/CircularProgress';
import { Link as RouterLink } from 'react-router-dom';
import MuiLink from '@mui/material/Link';
import { useConvertLead } from '../../hooks/useLeads';
import type { ConversionResult } from '../../types/contact';

interface Props {
  leadId: number;
  open: boolean;
  onClose: () => void;
}

export default function LeadConvertDialog({ leadId, open, onClose }: Props) {
  const [createAccount, setCreateAccount] = useState(true);
  const [createDeal, setCreateDeal] = useState(false);
  const [dealTitle, setDealTitle] = useState('');
  const [dealValue, setDealValue] = useState('');
  const [result, setResult] = useState<ConversionResult | null>(null);
  const convert = useConvertLead();

  const handleConvert = async () => {
    const res = await convert.mutateAsync({
      id: leadId,
      body: {
        create_account: createAccount,
        create_deal: createDeal,
        deal_title: createDeal ? dealTitle : undefined,
        deal_value: createDeal && dealValue ? Number(dealValue) : undefined,
      },
    });
    setResult(res);
  };

  const handleClose = () => {
    setResult(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>Convert Lead</DialogTitle>
      <DialogContent>
        {convert.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {(convert.error as Error).message}
          </Alert>
        )}
        {result ? (
          <Stack spacing={1}>
            <Typography variant="body2">Lead converted successfully.</Typography>
            <Typography variant="body2">Contact ID: {result.contact_id}</Typography>
            {result.account_id && <Typography variant="body2">Account ID: {result.account_id}</Typography>}
            {result.deal_id && <Typography variant="body2">Deal ID: {result.deal_id}</Typography>}
            <MuiLink component={RouterLink} to={`/contacts/${result.contact_id}`}>
              View Contact →
            </MuiLink>
          </Stack>
        ) : (
          <Stack spacing={1} sx={{ mt: 1 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={createAccount}
                  onChange={(e) => setCreateAccount(e.target.checked)}
                />
              }
              label="Create Account from company name"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={createDeal}
                  onChange={(e) => setCreateDeal(e.target.checked)}
                />
              }
              label="Create Deal stub"
            />
            {createDeal && (
              <>
                <TextField
                  label="Deal title"
                  value={dealTitle}
                  onChange={(e) => setDealTitle(e.target.value)}
                  required
                  size="small"
                />
                <TextField
                  label="Deal value"
                  type="number"
                  value={dealValue}
                  onChange={(e) => setDealValue(e.target.value)}
                  size="small"
                />
              </>
            )}
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        {!result && (
          <Button
            onClick={handleConvert}
            variant="contained"
            disabled={convert.isPending || (createDeal && !dealTitle)}
            startIcon={convert.isPending ? <CircularProgress size={16} /> : null}
          >
            Convert Lead
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
