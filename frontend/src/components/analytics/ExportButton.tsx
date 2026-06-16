import { useState } from 'react'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'

interface Props {
  onExport: () => Promise<void>
  label?: string
}

export default function ExportButton({ onExport, label = 'Export CSV' }: Props) {
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    setLoading(true)
    try {
      await onExport()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button variant="outlined" onClick={handleClick} disabled={loading} size="small">
      {loading ? <CircularProgress size={16} /> : label}
    </Button>
  )
}
