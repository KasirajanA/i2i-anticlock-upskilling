import type {
  Reply,
  Ticket,
  TicketFilters,
  TicketListResponse,
  SLARecord,
  ActivityLogEntry,
} from '../types/support'

const BASE = '/api/v1/support/tickets'

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const resp = await fetch(input, { credentials: 'include', ...init })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    const err = new Error(
      typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail),
    ) as Error & { status: number }
    err.status = resp.status
    throw err
  }
  return resp.json()
}

export function createTicket(payload: {
  subject: string
  description?: string
  priority: string
  contact_id: number
  assignee_id?: number
}): Promise<Ticket> {
  return request(BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getTicket(ticketId: number): Promise<Ticket> {
  return request(`${BASE}/${ticketId}`)
}

export function listTickets(
  params: TicketFilters & { cursor?: string; limit?: number },
): Promise<TicketListResponse> {
  const qs = new URLSearchParams()
  if (params.queue) qs.set('queue', params.queue)
  if (params.status) qs.set('status', params.status)
  if (params.priority) qs.set('priority', params.priority)
  if (params.assignee_id != null) qs.set('assignee_id', String(params.assignee_id))
  if (params.account_id != null) qs.set('account_id', String(params.account_id))
  if (params.created_after) qs.set('created_after', params.created_after)
  if (params.created_before) qs.set('created_before', params.created_before)
  if (params.cursor) qs.set('cursor', params.cursor)
  if (params.limit != null) qs.set('limit', String(params.limit))
  const q = qs.toString()
  return request(`${BASE}${q ? `?${q}` : ''}`)
}

export function updateTicket(
  ticketId: number,
  payload: { status?: string; priority?: string; assignee_id?: number },
): Promise<Ticket> {
  return request(`${BASE}/${ticketId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function assignTicket(ticketId: number, assignee_id: number): Promise<Ticket> {
  return request(`${BASE}/${ticketId}/assign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ assignee_id }),
  })
}

export function listReplies(
  ticketId: number,
): Promise<{ items: Reply[] }> {
  return request(`${BASE}/${ticketId}/replies`)
}

export function addReply(
  ticketId: number,
  body: string,
  is_internal = false,
): Promise<Reply> {
  return request(`${BASE}/${ticketId}/replies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ body, is_internal }),
  })
}

export function getActivity(ticketId: number): Promise<{ items: ActivityLogEntry[] }> {
  return request(`${BASE}/${ticketId}/activity`)
}

export function getSLARecords(ticketId: number): Promise<{ items: SLARecord[] }> {
  return request(`${BASE}/${ticketId}/sla`)
}
