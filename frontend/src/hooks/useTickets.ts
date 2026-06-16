import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { getTicket, listTickets } from '../services/supportApi'
import type { TicketFilters } from '../types/support'

export const TICKETS_KEY = 'tickets'

export function useTickets(params: TicketFilters & { limit?: number } = {}) {
  return useInfiniteQuery({
    queryKey: [TICKETS_KEY, params],
    queryFn: ({ pageParam }) =>
      listTickets({ ...params, cursor: pageParam as string | undefined }),
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    initialPageParam: undefined as string | undefined,
  })
}

export function useTicket(ticketId: number) {
  return useQuery({
    queryKey: [TICKETS_KEY, ticketId],
    queryFn: () => getTicket(ticketId),
    enabled: ticketId > 0,
  })
}
