import IconButton from '@mui/material/IconButton';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import ArchiveIcon from '@mui/icons-material/Archive';
import { Link as RouterLink } from 'react-router-dom';
import MuiLink from '@mui/material/Link';
import type { Contact } from '../../types/contact';

const MAX_TAGS = 3;

interface Props {
  contact: Contact;
  isAdmin: boolean;
  onArchive: (id: number) => void;
}

export default function ContactRow({ contact, isAdmin, onArchive }: Props) {
  const extraTags = contact.tags.length - MAX_TAGS;
  return (
    <TableRow hover>
      <TableCell>
        <MuiLink component={RouterLink} to={`/contacts/${contact.id}`} underline="hover">
          {contact.first_name} {contact.last_name}
        </MuiLink>
      </TableCell>
      <TableCell>{contact.email}</TableCell>
      <TableCell>
        {contact.primary_account ? (
          <Typography variant="body2" component="span">
            {contact.primary_account.name}
            {contact.primary_account.is_archived && (
              <Typography variant="caption" fontStyle="italic" sx={{ ml: 0.5 }}>
                (archived)
              </Typography>
            )}
          </Typography>
        ) : (
          '—'
        )}
      </TableCell>
      <TableCell>
        {contact.tags.slice(0, MAX_TAGS).map((tag) => (
          <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5 }} />
        ))}
        {extraTags > 0 && (
          <Tooltip title={contact.tags.slice(MAX_TAGS).join(', ')}>
            <Chip label={`+${extraTags} more`} size="small" variant="outlined" />
          </Tooltip>
        )}
      </TableCell>
      <TableCell>{contact.owner?.display_name ?? contact.owner?.name ?? '—'}</TableCell>
      <TableCell align="right">
        {isAdmin && (
          <IconButton size="small" onClick={() => onArchive(contact.id)} title="Archive">
            <ArchiveIcon fontSize="small" />
          </IconButton>
        )}
      </TableCell>
    </TableRow>
  );
}
