import type {
  ActivityLogResponse,
  CommentListResponse,
  Deal,
  DealCreateRequest,
  DealFilterParams,
  DealListResponse,
  DealUpdateRequest,
  ForecastResponse,
  StageChangeRequest,
  StageChangeResponse,
} from '../types/deal'

const DEALS_BASE = '/api/v1/deals'
const PIPELINE_BASE = '/api/v1/pipeline'

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const resp = await fetch(input, { credentials: 'include', ...init })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    const err = new Error(
      typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail),
    ) as Error & { status: number; code?: string }
    err.status = resp.status
    if (body.detail?.code) err.code = body.detail.code
    throw err
  }
  if (resp.status === 204) return undefined as T
  return resp.json()
}

export function listDeals(params: DealFilterParams = {}): Promise<DealListResponse> {
  const qs = new URLSearchParams()
  if (params.stage) qs.set('stage', params.stage)
  if (params.owner_id != null) qs.set('owner_id', String(params.owner_id))
  if (params.account_id != null) qs.set('account_id', String(params.account_id))
  if (params.is_overdue != null) qs.set('is_overdue', String(params.is_overdue))
  if (params.close_date_from) qs.set('close_date_from', params.close_date_from)
  if (params.close_date_to) qs.set('close_date_to', params.close_date_to)
  if (params.page != null) qs.set('page', String(params.page))
  if (params.limit != null) qs.set('limit', String(params.limit))
  const q = qs.toString()
  return request(`${DEALS_BASE}${q ? `?${q}` : ''}`)
}

export function getDeal(refId: string): Promise<Deal> {
  return request(`${DEALS_BASE}/${refId}`)
}

export function createDeal(payload: DealCreateRequest): Promise<Deal> {
  return request(DEALS_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateDeal(refId: string, payload: DealUpdateRequest): Promise<Deal> {
  return request(`${DEALS_BASE}/${refId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function changeDealStage(
  refId: string,
  payload: StageChangeRequest,
): Promise<StageChangeResponse> {
  return request(`${DEALS_BASE}/${refId}/stage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getComments(refId: string, page = 1, limit = 50): Promise<CommentListResponse> {
  return request(`${DEALS_BASE}/${refId}/comments?page=${page}&limit=${limit}`)
}

export function addComment(refId: string, body: string): Promise<import('../types/deal').DealComment> {
  return request(`${DEALS_BASE}/${refId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ body }),
  })
}

export function getActivity(refId: string): Promise<ActivityLogResponse> {
  return request(`${DEALS_BASE}/${refId}/activity`)
}

export function getForecast(period?: string): Promise<ForecastResponse> {
  const qs = period ? `?period=${encodeURIComponent(period)}` : ''
  return request(`${PIPELINE_BASE}/forecast${qs}`)
}
