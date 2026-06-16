import Timeline from '@mui/lab/Timeline';
import TimelineItem from '@mui/lab/TimelineItem';
import TimelineSeparator from '@mui/lab/TimelineSeparator';
import TimelineDot from '@mui/lab/TimelineDot';
import TimelineConnector from '@mui/lab/TimelineConnector';
import TimelineContent from '@mui/lab/TimelineContent';
import TimelineOppositeContent from '@mui/lab/TimelineOppositeContent';
import PersonIcon from '@mui/icons-material/Person';
import HandshakeIcon from '@mui/icons-material/Handshake';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import NoteIcon from '@mui/icons-material/Note';
import Skeleton from '@mui/material/Skeleton';
import Typography from '@mui/material/Typography';
import type { TimelineItem as TItem } from '../../types/contact';

const ICONS = {
  contact: <PersonIcon fontSize="small" />,
  deal: <HandshakeIcon fontSize="small" />,
  ticket: <SupportAgentIcon fontSize="small" />,
  note: <NoteIcon fontSize="small" />,
};

interface Props {
  items?: TItem[];
  isLoading?: boolean;
}

export default function AccountTimeline({ items, isLoading }: Props) {
  if (isLoading) {
    return (
      <>
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} variant="rectangular" height={48} sx={{ mb: 1 }} />
        ))}
      </>
    );
  }
  if (!items?.length) {
    return <Typography variant="body2" color="text.secondary">No activity yet.</Typography>;
  }
  return (
    <Timeline position="right">
      {items.map((item, idx) => (
        <TimelineItem key={`${item.type}-${item.id}`}>
          <TimelineOppositeContent sx={{ flex: 0.2 }} variant="caption" color="text.secondary">
            {new Date(item.created_at).toLocaleDateString()}
          </TimelineOppositeContent>
          <TimelineSeparator>
            <TimelineDot color="primary" variant="outlined">
              {ICONS[item.type] ?? <NoteIcon fontSize="small" />}
            </TimelineDot>
            {idx < items.length - 1 && <TimelineConnector />}
          </TimelineSeparator>
          <TimelineContent>
            <Typography variant="body2">{item.label}</Typography>
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  );
}
