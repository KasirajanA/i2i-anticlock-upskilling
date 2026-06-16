import Chip, { type ChipProps } from '@mui/material/Chip'
import type { ContractStatus } from '../../types/contracts'

const STATUS_COLORS: Record<ContractStatus, ChipProps['color']> = {
  Draft: 'default',
  'Sent for Review': 'info',
  Active: 'success',
  Expired: 'warning',
  Terminated: 'error',
}

interface Props {
  status: ContractStatus
  size?: ChipProps['size']
}

export default function ContractStatusChip({ status, size = 'small' }: Props) {
  return (
    <Chip
      label={status}
      color={STATUS_COLORS[status]}
      size={size}
      aria-label={`Contract status: ${status}`}
    />
  )
}
