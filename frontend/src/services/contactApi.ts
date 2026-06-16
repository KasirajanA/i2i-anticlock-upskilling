import type {
  Contact,
  ContactDetail,
  ContactCreateResult,
  PaginatedContacts,
  ContactFilters,
  Account,
  AccountDetail,
  PaginatedAccounts,
  AccountFilters,
  TimelineItem,
  Lead,
  PaginatedLeads,
  LeadFilters,
  ConvertLeadRequest,
  ConversionResult,
  ImportResult,
  Segment,
  FilterSpec,
} from '../types/contact';

async function request<T>(input: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(input, { credentials: 'include', ...init });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }));
    const err = new Error(body.detail ?? 'Request failed') as Error & { status: number };
    err.status = resp.status;
    throw err;
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

function qs(params: Record<string, unknown>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : '';
}

// ── Contacts ──────────────────────────────────────────────────────────────────

export function listContacts(params: ContactFilters = {}): Promise<PaginatedContacts> {
  return request(`/api/v1/contacts${qs(params as Record<string, unknown>)}`);
}

export function getContact(id: number): Promise<ContactDetail> {
  return request(`/api/v1/contacts/${id}`);
}

export function createContact(body: {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  job_title?: string;
  account_ids: number[];
  tags: string[];
}): Promise<ContactCreateResult> {
  return request('/api/v1/contacts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function updateContact(id: number, body: Partial<Contact>): Promise<Contact> {
  return request(`/api/v1/contacts/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function archiveContact(id: number): Promise<void> {
  return request(`/api/v1/contacts/${id}`, { method: 'DELETE' });
}

export function importContacts(file: File, duplicate_mode: 'skip' | 'overwrite' = 'skip'): Promise<ImportResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('duplicate_mode', duplicate_mode);
  return request('/api/v1/contacts/import', { method: 'POST', body: form });
}

// ── Accounts ──────────────────────────────────────────────────────────────────

export function listAccounts(params: AccountFilters = {}): Promise<PaginatedAccounts> {
  return request(`/api/v1/accounts${qs(params as Record<string, unknown>)}`);
}

export function getAccount(id: number): Promise<AccountDetail> {
  return request(`/api/v1/accounts/${id}`);
}

export function createAccount(body: {
  name: string;
  industry?: string;
  company_size?: string;
  website?: string;
  billing_address?: string;
}): Promise<Account> {
  return request('/api/v1/accounts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function updateAccount(id: number, body: Partial<Account>): Promise<Account> {
  return request(`/api/v1/accounts/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function archiveAccount(id: number): Promise<void> {
  return request(`/api/v1/accounts/${id}`, { method: 'DELETE' });
}

export function getAccountTimeline(id: number): Promise<TimelineItem[]> {
  return request(`/api/v1/accounts/${id}/timeline`);
}

// ── Leads ─────────────────────────────────────────────────────────────────────

export function listLeads(params: LeadFilters = {}): Promise<PaginatedLeads> {
  return request(`/api/v1/leads${qs(params as Record<string, unknown>)}`);
}

export function getLead(id: number): Promise<Lead> {
  return request(`/api/v1/leads/${id}`);
}

export function createLead(body: {
  first_name: string;
  last_name: string;
  email: string;
  company_name?: string;
  notes?: string;
  owner_id?: number;
}): Promise<Lead> {
  return request('/api/v1/leads', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function updateLead(id: number, body: { status: string; disqualify_reason?: string }): Promise<Lead> {
  return request(`/api/v1/leads/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function convertLead(id: number, body: ConvertLeadRequest): Promise<ConversionResult> {
  return request(`/api/v1/leads/${id}/convert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ── Segments ──────────────────────────────────────────────────────────────────

export function listSegments(entity_type: string): Promise<Segment[]> {
  return request(`/api/v1/segments${qs({ entity_type })}`);
}

export function createSegment(body: {
  name: string;
  entity_type: string;
  filter_spec: FilterSpec;
}): Promise<Segment> {
  return request('/api/v1/segments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function getSegmentCount(id: number): Promise<{ count: number }> {
  return request(`/api/v1/segments/${id}/count`);
}
