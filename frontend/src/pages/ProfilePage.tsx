import { useState } from 'react'
import Accordion from '@mui/material/Accordion'
import AccordionDetails from '@mui/material/AccordionDetails'
import AccordionSummary from '@mui/material/AccordionSummary'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import AvatarUpload from '../components/users/AvatarUpload'
import { useChangePassword, useMe, useUpdateMe, useUploadAvatar } from '../hooks/useUsers'

export default function ProfilePage() {
  const { data: me, isLoading } = useMe()
  const updateMe = useUpdateMe()
  const uploadAvatar = useUploadAvatar()
  const changePassword = useChangePassword()

  const [displayName, setDisplayName] = useState('')
  const [timezone, setTimezone] = useState('')
  const [profileSaved, setProfileSaved] = useState(false)

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [pwError, setPwError] = useState<string | null>(null)
  const [pwSaved, setPwSaved] = useState(false)

  if (isLoading) return <CircularProgress sx={{ m: 4 }} />
  if (!me) return null

  async function handleProfileSave() {
    setProfileSaved(false)
    await updateMe.mutateAsync({
      display_name: displayName || undefined,
      timezone: timezone || undefined,
    })
    setProfileSaved(true)
  }

  async function handlePasswordChange() {
    setPwError(null)
    setPwSaved(false)
    try {
      await changePassword.mutateAsync({ current_password: currentPw, new_password: newPw })
      setPwSaved(true)
      setCurrentPw('')
      setNewPw('')
    } catch (err: unknown) {
      setPwError(err instanceof Error ? err.message : 'Failed to change password.')
    }
  }

  return (
    <Box sx={{ p: 3, maxWidth: 600 }}>
      <Typography variant="h5" mb={3}>Profile</Typography>

      <AvatarUpload
        currentUrl={me.avatar_url}
        onUpload={(file) => uploadAvatar.mutateAsync(file)}
      />

      <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          label="Display Name"
          value={displayName || me.display_name || ''}
          onChange={(e) => setDisplayName(e.target.value)}
          inputProps={{ maxLength: 100 }}
        />
        <TextField
          label="Timezone"
          value={timezone || me.timezone || ''}
          onChange={(e) => setTimezone(e.target.value)}
          helperText="IANA timezone, e.g. America/New_York"
        />
        {profileSaved && <Alert severity="success">Profile saved.</Alert>}
        <Button variant="contained" onClick={handleProfileSave} disabled={updateMe.isPending}>
          Save Profile
        </Button>
      </Box>

      <Accordion sx={{ mt: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Change Password</Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Current Password"
            type="password"
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
          />
          <TextField
            label="New Password"
            type="password"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            helperText="Minimum 8 characters"
          />
          {pwError && <Alert severity="error">{pwError}</Alert>}
          {pwSaved && <Alert severity="success">Password changed.</Alert>}
          <Button variant="contained" onClick={handlePasswordChange} disabled={changePassword.isPending}>
            Change Password
          </Button>
        </AccordionDetails>
      </Accordion>
    </Box>
  )
}
