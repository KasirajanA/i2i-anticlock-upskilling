import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  addReply,
  assignTicket,
  createTicket,
  updateTicket,
} from '../services/supportApi'
import { TICKETS_KEY } from './useTickets'

export function useCreateTicket() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createTicket,
    onSuccess: () => qc.invalidateQueries({ queryKey: [TICKETS_KEY] }),
  })
}

export function useUpdateTicket(ticketId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: { status?: string; priority?: string; assignee_id?: number }) =>
      updateTicket(ticketId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TICKETS_KEY] }),
  })
}

export function useAddReply(ticketId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ body, is_internal }: { body: string; is_internal?: boolean }) =>
      addReply(ticketId, body, is_internal),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [TICKETS_KEY, ticketId] })
      qc.invalidateQueries({ queryKey: ['replies', ticketId] })
    },
  })
}

export function useAssignTicket(ticketId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (assignee_id: number) => assignTicket(ticketId, assignee_id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TICKETS_KEY] }),
  })
}
