import type {
  ActivityLogResponse,
  Contract,
  ContractCreateRequest,
  ContractFilterParams,
  ContractListResponse,
  ContractUpdateRequest,
  RenewResponse,
  TransitionRequest,
  TransitionResponse,
} from '../types/contracts'

const BASE = '/api/v1/contracts'

async function request<T>(
  input: RequestInfo,
  init?: RequestInit,
): Promise<T> {
  const resp = await fetch(input, { credentials: 'include', ...init })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    const err = new Error(body.detail ?? 'Request failed') as Error & { status: number }
    err.status = resp.status
    throw err
  }
  if (resp.status === 204) return undefined as T
  return resp.json()
}

export function listContracts(params: ContractFilterParams = {}): Promise<ContractListResponse> {
  const qs = new URLSearchParams()
  if (params.status) qs.set('status', params.status)
  if (params.owner != null) qs.set('owner', String(params.owner))
  if (params.account_id != null) qs.set('account_id', String(params.account_id))
  if (params.end_date_from) qs.set('end_date_from', params.end_date_from)
  if (params.end_date_to) qs.set('end_date_to', params.end_date_to)
  if (params.is_renewal_due != null) qs.set('is_renewal_due', String(params.is_renewal_due))
  if (params.page != null) qs.set('page', String(params.page))
  if (params.limit != null) qs.set('limit', String(params.limit))
  const query = qs.toString()
  return request(`${BASE}${query ? `?${query}` : ''}`)
}

export function getContract(refId: string): Promise<Contract> {
  return request(`${BASE}/${refId}`)
}

export function createContract(payload: ContractCreateRequest): Promise<Contract> {
  return request(BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateContract(
  refId: string,
  payload: ContractUpdateRequest,
): Promise<Contract> {
  return request(`${BASE}/${refId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function transitionContract(
  refId: string,
  payload: TransitionRequest,
): Promise<TransitionResponse> {
  return request(`${BASE}/${refId}/transition`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getActivityLog(refId: string): Promise<ActivityLogResponse> {
  return request(`${BASE}/${refId}/activity`)
}

export function renewContract(refId: string): Promise<RenewResponse> {
  return request(`${BASE}/${refId}/renew`, { method: 'POST' })
}

export function uploadAttachment(refId: string, file: File): Promise<unknown> {
  const form = new FormData()
  form.append('file', file)
  return request(`${BASE}/${refId}/attachment`, { method: 'POST', body: form })
}

export function deleteAttachment(refId: string): Promise<void> {
  return request(`${BASE}/${refId}/attachment`, { method: 'DELETE' })
}
