import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import { Link as RouterLink } from 'react-router-dom';
import type { DuplicateWarning } from '../../types/contact';

interface Props {
  warning: DuplicateWarning;
  onClose: () => void;
}

export default function DuplicateWarningBanner({ warning, onClose }: Props) {
  return (
    <Alert severity="warning" onClose={onClose} sx={{ mb: 2 }}>
      {warning.message}{' '}
      <Link component={RouterLink} to={`/contacts/${warning.existing_id}`}>
        View existing contact
      </Link>
    </Alert>
  );
}
