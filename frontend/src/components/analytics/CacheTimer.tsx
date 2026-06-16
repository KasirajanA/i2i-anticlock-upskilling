import Typography from '@mui/material/Typography'

interface Props {
  cached_until: string | null
}

export default function CacheTimer({ cached_until }: Props) {
  if (!cached_until) return null
  const diff = Math.max(0, Math.round((new Date(cached_until).getTime() - Date.now()) / 1000))
  const label = diff >= 60 ? `${Math.floor(diff / 60)} min` : `${diff}s`
  return (
    <Typography variant="caption" color="text.secondary">
      Refreshing in {label}
    </Typography>
  )
}
