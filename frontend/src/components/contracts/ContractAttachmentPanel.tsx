import AttachFileIcon from '@mui/icons-material/AttachFile'
import DeleteIcon from '@mui/icons-material/Delete'
import UploadIcon from '@mui/icons-material/Upload'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import IconButton from '@mui/material/IconButton'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { useRef, useState } from 'react'
import type { ContractAttachment } from '../../types/contracts'
import { useAttachmentMutation } from '../../hooks/useContracts'

const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'image/jpeg',
  'image/png',
]
const MAX_BYTES = 1_048_576

interface Props {
  refId: string
  attachment: ContractAttachment | null
  canEdit: boolean
}

export default function ContractAttachmentPanel({ refId, attachment, canEdit }: Props) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [localError, setLocalError] = useState<string | null>(null)
  const { upload, remove } = useAttachmentMutation(refId)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLocalError(null)

    if (!ALLOWED_TYPES.includes(file.type)) {
      setLocalError('Only PDF, DOCX, JPEG, and PNG files are accepted.')
      return
    }
    if (file.size > MAX_BYTES) {
      setLocalError('File must be under 1 MB.')
      return
    }
    upload.mutate(file)
    e.target.value = ''
  }

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Attachment
      </Typography>

      {localError && (
        <Alert severity="error" sx={{ mb: 1 }} onClose={() => setLocalError(null)}>
          {localError}
        </Alert>
      )}
      {upload.isError && (
        <Alert severity="error" sx={{ mb: 1 }}>
          {(upload.error as Error).message}
        </Alert>
      )}

      {attachment ? (
        <Stack direction="row" alignItems="center" spacing={1}>
          <AttachFileIcon fontSize="small" />
          <Typography variant="body2">{attachment.filename}</Typography>
          <Typography variant="caption" color="text.secondary">
            ({(attachment.size_bytes / 1024).toFixed(1)} KB)
          </Typography>
          {canEdit && (
            <>
              <Tooltip title="Replace attachment">
                <IconButton
                  size="small"
                  onClick={() => fileRef.current?.click()}
                  disabled={upload.isPending || remove.isPending}
                  aria-label="Replace attachment"
                >
                  <UploadIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete attachment">
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => remove.mutate()}
                  disabled={upload.isPending || remove.isPending}
                  aria-label="Delete attachment"
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Stack>
      ) : (
        canEdit && (
          <Button
            variant="outlined"
            size="small"
            startIcon={upload.isPending ? <CircularProgress size={16} /> : <UploadIcon />}
            onClick={() => fileRef.current?.click()}
            disabled={upload.isPending}
            aria-label="Upload attachment"
          >
            Upload file
          </Button>
        )
      )}

      {!attachment && !canEdit && (
        <Typography variant="body2" color="text.secondary">
          No attachment.
        </Typography>
      )}

      <input
        ref={fileRef}
        type="file"
        hidden
        accept=".pdf,.docx,.jpg,.jpeg,.png"
        onChange={handleFileChange}
        aria-hidden="true"
      />
    </Box>
  )
}
