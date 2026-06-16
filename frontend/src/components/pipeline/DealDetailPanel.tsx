import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import Drawer from '@mui/material/Drawer'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useState } from 'react'
import { useAddComment, useComments } from '../../hooks/useComments'
import { useDeal } from '../../hooks/useDeals'
import type { DealSummary } from '../../types/deal'

interface Props {
  deal: DealSummary | null
  onClose: () => void
}

export default function DealDetailPanel({ deal, onClose }: Props) {
  const open = Boolean(deal)
  const { data: full, isLoading: loadingDeal } = useDeal(deal?.ref_id ?? '')
  const { data: comments, isLoading: loadingComments } = useComments(deal?.ref_id ?? '')
  const addComment = useAddComment(deal?.ref_id ?? '')
  const [commentBody, setCommentBody] = useState('')

  async function submitComment() {
    if (!commentBody.trim()) return
    await addComment.mutateAsync(commentBody.trim())
    setCommentBody('')
  }

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 380, p: 3 }}>
        {!deal ? null : loadingDeal ? (
          <CircularProgress />
        ) : full ? (
          <>
            <Typography variant="h6">{full.title}</Typography>
            <Chip
              label={full.stage}
              size="small"
              color={full.is_overdue ? 'warning' : 'default'}
              sx={{ mb: 1 }}
            />
            <Typography variant="body2">
              Value: ${Number(full.value).toLocaleString()}
            </Typography>
            <Typography variant="body2">
              Close: {full.expected_close_date}
            </Typography>
            <Typography variant="body2">Owner: {full.owner.name}</Typography>
            <Typography variant="body2">Account: {full.account.name}</Typography>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Comments
            </Typography>
            {loadingComments ? (
              <CircularProgress size={16} />
            ) : (
              comments?.items.map((c) => (
                <Box key={c.id} sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {c.author.name} · {c.created_at.slice(0, 10)}
                  </Typography>
                  <Typography variant="body2">{c.body}</Typography>
                </Box>
              ))
            )}
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <TextField
                size="small"
                fullWidth
                placeholder="Add comment…"
                value={commentBody}
                onChange={(e) => setCommentBody(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    submitComment()
                  }
                }}
              />
              <Button size="small" onClick={submitComment} disabled={!commentBody.trim()}>
                Add
              </Button>
            </Box>
          </>
        ) : null}
      </Box>
    </Drawer>
  )
}
