export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'converted' | 'disqualified';

export interface AccountSummary {
  id: number;
  name: string;
  is_archived: boolean;
}

export interface OwnerSummary {
  id: number;
  name: string;
  display_name?: string;
}

export interface Contact {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  job_title?: string;
  primary_account?: AccountSummary;
  tags: string[];
  owner?: OwnerSummary;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomFieldValue {
  key: string;
  label: string;
  value: string | null;
}

export interface ContactDetail extends Contact {
  accounts: (AccountSummary & { linked_at: string })[];
  custom_fields: CustomFieldValue[];
}

export interface Account {
  id: number;
  name: string;
  industry?: string;
  company_size?: string;
  website?: string;
  billing_address?: string;
  owner?: OwnerSummary;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountDetail extends Account {
  contact_count: number;
}

export interface TimelineItem {
  type: 'contact' | 'deal' | 'ticket' | 'note';
  id: number;
  label: string;
  created_at: string;
}

export interface Lead {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  company_name?: string;
  status: LeadStatus;
  disqualify_reason?: string;
  notes?: string;
  owner_id?: number;
  converted_contact_id?: number;
  created_at: string;
  updated_at: string;
}

export interface Segment {
  id: number;
  name: string;
  entity_type: string;
  filter_spec: FilterSpec;
  live_count: number;
  created_at: string;
}

export interface FilterCondition {
  field: string;
  operator: 'eq' | 'contains' | 'in';
  value: string;
}

export interface FilterSpec {
  conditions: FilterCondition[];
}

export interface ImportResult {
  imported: number;
  skipped: number;
  errors: number;
  error_details: { row: number; reason: string }[];
}

export interface DuplicateWarning {
  existing_id: number;
  existing_email: string;
  message: string;
}

export interface ContactCreateResult {
  contact?: ContactDetail;
  duplicate_warning?: DuplicateWarning;
}

export interface ConvertLeadRequest {
  create_account: boolean;
  create_deal: boolean;
  deal_title?: string;
  deal_value?: number;
}

export interface ConversionResult {
  contact_id: number;
  account_id?: number;
  deal_id?: number;
  lead_id: number;
}

export interface ContactFilters {
  q?: string;
  account_id?: number;
  tag?: string;
  owner_id?: number;
  include_archived?: boolean;
  cursor?: string;
  limit?: number;
}

export interface AccountFilters {
  q?: string;
  industry?: string;
  owner_id?: number;
  include_archived?: boolean;
  cursor?: string;
  limit?: number;
}

export interface LeadFilters {
  status?: LeadStatus;
  q?: string;
  limit?: number;
}

export interface PaginatedContacts {
  items: Contact[];
  total: number;
  next_cursor?: string;
}

export interface PaginatedAccounts {
  items: Account[];
  total: number;
  next_cursor?: string;
}

export interface PaginatedLeads {
  items: Lead[];
  total: number;
  next_cursor?: string;
}
