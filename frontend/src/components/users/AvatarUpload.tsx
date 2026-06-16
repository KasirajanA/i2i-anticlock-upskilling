import { useRef, useState } from 'react'
import Avatar from '@mui/material/Avatar'
import Box from '@mui/material/Box'
import FormHelperText from '@mui/material/FormHelperText'
import LinearProgress from '@mui/material/LinearProgress'
import Typography from '@mui/material/Typography'

const ALLOWED_MIME = new Set(['image/jpeg', 'image/png', 'image/webp'])
const MAX_BYTES = 2 * 1024 * 1024

interface Props {
  currentUrl?: string | null
  onUpload: (file: File) => Promise<void>
}

export default function AvatarUpload({ currentUrl, onUpload }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  async function handleFile(file: File) {
    setError(null)
    if (!ALLOWED_MIME.has(file.type)) {
      setError('Only JPEG, PNG, or WebP images are allowed.')
      return
    }
    if (file.size > MAX_BYTES) {
      setError('File must be 2 MB or smaller.')
      return
    }
    setUploading(true)
    try {
      await onUpload(file)
    } catch {
      setError('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <Box>
      <Box
        sx={{
          border: '2px dashed',
          borderColor: 'divider',
          borderRadius: 2,
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          cursor: 'pointer',
          '&:hover': { borderColor: 'primary.main' },
        }}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <Avatar
          src={currentUrl ?? undefined}
          sx={{ width: 80, height: 80, mb: 1 }}
        />
        <Typography variant="caption" color="text.secondary">
          Click or drag to upload avatar
        </Typography>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
        />
      </Box>
      {uploading && <LinearProgress sx={{ mt: 1 }} />}
      {error && <FormHelperText error>{error}</FormHelperText>}
    </Box>
  )
}
