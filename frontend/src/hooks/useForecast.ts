import { useQuery } from '@tanstack/react-query'
import { getForecast } from '../services/dealService'

export function useForecast(period?: string) {
  return useQuery({
    queryKey: ['forecast', period ?? 'current'],
    queryFn: () => getForecast(period),
  })
}
