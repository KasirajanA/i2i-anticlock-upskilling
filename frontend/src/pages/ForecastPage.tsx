import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import ButtonGroup from '@mui/material/ButtonGroup'
import CircularProgress from '@mui/material/CircularProgress'
import Typography from '@mui/material/Typography'
import { useState } from 'react'
import ForecastTable from '../components/pipeline/ForecastTable'
import { useForecast } from '../hooks/useForecast'

function currentQuarterPeriod(): string {
  const now = new Date()
  const q = Math.floor(now.getMonth() / 3)
  const year = now.getFullYear()
  const starts = ['-01-01', '-04-01', '-07-01', '-10-01']
  const ends = ['-03-31', '-06-30', '-09-30', '-12-31']
  return `${year}${starts[q]}/${year}${ends[q]}`
}

function nextQuarterPeriod(): string {
  const now = new Date()
  const q = Math.floor(now.getMonth() / 3)
  const year = now.getFullYear()
  const starts = ['-01-01', '-04-01', '-07-01', '-10-01']
  const ends = ['-03-31', '-06-30', '-09-30', '-12-31']
  const next = (q + 1) % 4
  const nextYear = next === 0 ? year + 1 : year
  return `${nextYear}${starts[next]}/${nextYear}${ends[next]}`
}

export default function ForecastPage() {
  const [period, setPeriod] = useState<string | undefined>(undefined)
  const { data, isLoading, error } = useForecast(period)

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Forecast
      </Typography>
      <ButtonGroup variant="outlined" size="small" sx={{ mb: 2 }}>
        <Button onClick={() => setPeriod(undefined)}>Current Quarter</Button>
        <Button onClick={() => setPeriod(currentQuarterPeriod())}>This Quarter</Button>
        <Button onClick={() => setPeriod(nextQuarterPeriod())}>Next Quarter</Button>
      </ButtonGroup>
      {isLoading && <CircularProgress />}
      {error && (
        <Typography color="error">{(error as Error).message}</Typography>
      )}
      {data && <ForecastTable data={data} />}
    </Box>
  )
}
