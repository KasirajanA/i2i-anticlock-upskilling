import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import type { LeadStatus } from '../../types/contact';

const COLOR_MAP: Record<LeadStatus, ChipProps['color']> = {
  new: 'default',
  contacted: 'info',
  qualified: 'warning',
  converted: 'success',
  disqualified: 'error',
};

interface Props {
  status: LeadStatus;
}

export default function LeadStatusChip({ status }: Props) {
  return <Chip label={status} color={COLOR_MAP[status]} size="small" variant="filled" />;
}
