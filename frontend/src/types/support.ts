export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed'
export type TicketPriority = 'low' | 'medium' | 'high' | 'critical'

export interface SLARecord {
  id: number
  cycle: number
  first_response_due: string
  resolution_due: string
  first_response_at: string | null
  resolved_at: string | null
  first_response_breached: boolean
  resolution_breached: boolean
  is_active: boolean
}

export interface SLASummary {
  first_response_due: string
  resolution_due: string
  first_response_breached: boolean
  resolution_breached: boolean
  warning: boolean
}

export interface Ticket {
  id: number
  ref: string
  subject: string
  description: string | null
  status: TicketStatus
  priority: TicketPriority
  contact_id: number | null
  contact_name_snapshot: string
  account_id: number | null
  assignee_id: number | null
  created_by_id: number
  sla: SLARecord | null
  created_at: string
  updated_at: string
}

export interface TicketSummary {
  id: number
  ref: string
  subject: string
  status: TicketStatus
  priority: TicketPriority
  contact_name: string
  assignee_id: number | null
  sla: SLASummary | null
  created_at: string
  updated_at: string
}

export interface TicketListResponse {
  items: TicketSummary[]
  next_cursor: string | null
  total: number
}

export interface Reply {
  id: number
  ticket_id: number
  author_id: number
  body: string
  is_internal: boolean
  created_at: string
}

export interface ActivityLogEntry {
  id: number
  event_type: string
  actor_id: number | null
  event_metadata: Record<string, unknown> | null
  created_at: string
}

export interface TicketFilters {
  queue?: 'mine' | 'unassigned' | 'all'
  status?: TicketStatus
  priority?: TicketPriority
  assignee_id?: number
  account_id?: number
  created_after?: string
  created_before?: string
}
