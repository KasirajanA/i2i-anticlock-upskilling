import Autocomplete from '@mui/material/Autocomplete'
import Chip from '@mui/material/Chip'
import TextField from '@mui/material/TextField'
import { useUserList } from '../../hooks/useUsers'
import type { UserProfile } from '../../types/user'

interface Props {
  value: UserProfile[]
  onChange: (users: UserProfile[]) => void
  label?: string
}

export default function MemberPicker({ value, onChange, label = 'Members' }: Props) {
  const { data } = useUserList()
  const users = data?.items ?? []

  return (
    <Autocomplete
      multiple
      options={users}
      value={value}
      onChange={(_e, next) => onChange(next)}
      getOptionLabel={(u) => u.display_name ?? u.name}
      isOptionEqualToValue={(a, b) => a.id === b.id}
      filterOptions={(opts, state) => {
        const q = state.inputValue.toLowerCase()
        return opts.filter(
          (u) =>
            (u.display_name ?? u.name).toLowerCase().includes(q) ||
            u.email.toLowerCase().includes(q),
        )
      }}
      renderTags={(selected, getTagProps) =>
        selected.map((u, i) => (
          <Chip key={u.id} label={u.display_name ?? u.name} {...getTagProps({ index: i })} />
        ))
      }
      renderInput={(params) => <TextField {...params} label={label} />}
    />
  )
}
