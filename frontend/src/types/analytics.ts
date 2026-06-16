export interface DashboardWidget {
  key: string
  label: string
  value: number
  unit?: string
}

export interface DashboardResponse {
  widgets: DashboardWidget[]
  generated_at: string
}

export interface StageBreakdown {
  stage: string
  count: number
  total_value: string
}

export interface RepRevenue {
  owner_id: number
  owner_name: string
  revenue: string
}

export interface SalesReportResponse {
  stage_breakdown: StageBreakdown[]
  won_count: number
  lost_count: number
  avg_deal_value: string | null
  top_reps: RepRevenue[]
  filters_applied: ReportFiltersApplied
  cached_until: string | null
}

export interface StatusBreakdown {
  status: string
  count: number
}

export interface PriorityBreakdown {
  priority: string
  count: number
}

export interface PerAgentCount {
  assignee_id: number | null
  assignee_name: string
  count: number
}

export interface SupportReportResponse {
  status_breakdown: StatusBreakdown[]
  priority_breakdown: PriorityBreakdown[]
  avg_resolution_hours: number | null
  sla_breach_rate: number | null
  per_agent: PerAgentCount[]
  filters_applied: ReportFiltersApplied
  cached_until: string | null
}

export interface UpcomingRenewal {
  contract_id: number
  ref_id: string
  account_name: string
  value: string
  expiry_date: string
  days_remaining: number
}

export interface AccountValue {
  account_id: number | null
  account_name: string
  total_value: string
}

export interface ContractReportResponse {
  status_breakdown: { status: string; count: number; total_value: string }[]
  upcoming_renewals: UpcomingRenewal[]
  value_by_account: AccountValue[]
  filters_applied: ReportFiltersApplied
  cached_until: string | null
}

export interface ReportFiltersApplied {
  created_after?: string | null
  created_before?: string | null
  owner_id?: number | null
  assignee_id?: number | null
  renewal_window?: number | null
}

export interface ReportFilters {
  created_after?: string
  created_before?: string
  owner_id?: number
  assignee_id?: number
}

export interface ContractFilters {
  renewal_window?: 30 | 60 | 90
  owner_id?: number
}
