import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Chip from '@mui/material/Chip'
import Typography from '@mui/material/Typography'
import GroupIcon from '@mui/icons-material/Group'
import type { Team } from '../../types/user'

interface Props {
  team: Team
  onClick?: () => void
}

export default function TeamCard({ team, onClick }: Props) {
  return (
    <Card
      variant="outlined"
      sx={{ cursor: onClick ? 'pointer' : 'default' }}
      onClick={onClick}
    >
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {team.name}
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {team.lead_user_id ? `Lead: user #${team.lead_user_id}` : 'No lead assigned'}
        </Typography>
        <Chip icon={<GroupIcon />} label={`${team.member_count} members`} size="small" />
      </CardContent>
    </Card>
  )
}
