export type ContractStatus =
  | 'Draft'
  | 'Sent for Review'
  | 'Active'
  | 'Expired'
  | 'Terminated'

export interface ContractAttachment {
  id: number
  contract_id: number
  filename: string
  mime_type: string
  size_bytes: number
  created_at: string
}

export interface Contract {
  id: number
  ref_id: string
  value: string
  start_date: string
  end_date: string
  status: ContractStatus
  description: string | null
  is_renewal_due: boolean
  is_archived: boolean
  owner_id: number
  account_id: number
  deal_id: number | null
  created_at: string
  updated_at: string
  attachment: ContractAttachment | null
}

export interface ContractListItem {
  id: number
  ref_id: string
  value: string
  start_date: string
  end_date: string
  status: ContractStatus
  is_renewal_due: boolean
  is_archived: boolean
  owner_id: number
  account_id: number
  deal_id: number | null
  created_at: string
  updated_at: string
}

export interface ContractListResponse {
  total: number
  page: number
  limit: number
  items: ContractListItem[]
}

export interface ActivityLog {
  id: number
  action_type: string
  actor_id: number
  actor_name: string
  note: string | null
  created_at: string
}

export interface ActivityLogResponse {
  ref_id: string
  logs: ActivityLog[]
}

export interface RenewalLink {
  id: number
  original_contract_id: number
  successor_contract_id: number
  created_at: string
}

export interface TransitionRequest {
  status: ContractStatus
  note?: string
}

export interface TransitionResponse {
  ref_id: string
  previous_status: ContractStatus
  new_status: ContractStatus
  logged_at: string
}

export interface RenewResponse {
  original_ref_id: string
  successor: Contract
}

export interface ContractCreateRequest {
  value: number
  start_date: string
  end_date: string
  description?: string
  account_id: number
  deal_id?: number
  owner_id?: number
}

export interface ContractUpdateRequest {
  value?: number
  start_date?: string
  end_date?: string
  description?: string
  deal_id?: number
}

export interface ContractFilterParams {
  status?: ContractStatus
  owner?: number
  account_id?: number
  end_date_from?: string
  end_date_to?: string
  is_renewal_due?: boolean
  page?: number
  limit?: number
}
