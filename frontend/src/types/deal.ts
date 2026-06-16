export type DealStage =
  | 'Lead In'
  | 'Qualified'
  | 'Proposal'
  | 'Negotiation'
  | 'Closed Won'
  | 'Closed Lost'

export const DEAL_STAGES: DealStage[] = [
  'Lead In',
  'Qualified',
  'Proposal',
  'Negotiation',
  'Closed Won',
  'Closed Lost',
]

export const OPEN_STAGES: DealStage[] = [
  'Lead In',
  'Qualified',
  'Proposal',
  'Negotiation',
]

export interface UserRef {
  id: number
  name: string
  email: string
}

export interface AccountRef {
  id: number
  name: string
}

export interface ContactRef {
  id: number
  name: string
}

export interface Deal {
  id: number
  ref_id: string
  title: string
  value: string
  stage: DealStage
  expected_close_date: string
  is_overdue: boolean
  is_archived: boolean
  loss_reason: string | null
  owner: UserRef
  account: AccountRef
  contact: ContactRef | null
  created_at: string
  updated_at: string
}

export interface DealSummary {
  id: number
  ref_id: string
  title: string
  value: string
  stage: DealStage
  expected_close_date: string
  is_overdue: boolean
  owner: UserRef
  account: AccountRef
}

export interface DealListResponse {
  total: number
  page: number
  limit: number
  items: DealSummary[]
}

export interface DealCreateRequest {
  title: string
  value: string
  stage: DealStage
  expected_close_date: string
  owner_id: number
  account_id: number
  contact_id?: number | null
}

export interface DealUpdateRequest {
  title?: string
  value?: string
  expected_close_date?: string
  contact_id?: number | null
}

export interface StageChangeRequest {
  stage: DealStage
  loss_reason?: string | null
}

export interface StageChangeResponse {
  ref_id: string
  previous_stage: DealStage
  new_stage: DealStage
  is_overdue: boolean
  updated_at: string
}

export interface DealComment {
  id: number
  body: string
  author: UserRef
  created_at: string
}

export interface CommentListResponse {
  total: number
  page: number
  limit: number
  items: DealComment[]
}

export interface ActivityLog {
  id: number
  action_type: string
  note: string | null
  actor: UserRef | null
  created_at: string
}

export interface ActivityLogResponse {
  total: number
  items: ActivityLog[]
}

export interface StageTotal {
  stage: DealStage
  deal_count: number
  total_value: string
  probability: string
  weighted_value: string
}

export interface ClosedWonTotal {
  deal_count: number
  total_value: string
}

export interface ForecastResponse {
  period_start: string
  period_end: string
  open_pipeline: StageTotal[]
  closed_won: ClosedWonTotal
  total_weighted_forecast: string
}

export interface DealFilterParams {
  stage?: DealStage
  owner_id?: number
  account_id?: number
  is_overdue?: boolean
  close_date_from?: string
  close_date_to?: string
  page?: number
  limit?: number
}
