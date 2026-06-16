import type {
  ContractFilters,
  ContractReportResponse,
  DashboardResponse,
  ReportFilters,
  SalesReportResponse,
  SupportReportResponse,
} from '../types/analytics'

const BASE = '/api/v1/analytics'

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

function toQS(params: Record<string, string | number | undefined | null>): string {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v != null) qs.set(k, String(v))
  }
  const s = qs.toString()
  return s ? `?${s}` : ''
}

export function getDashboard(): Promise<DashboardResponse> {
  return request(`${BASE}/dashboard`)
}

export function getSalesReport(filters: ReportFilters = {}): Promise<SalesReportResponse> {
  return request(`${BASE}/reports/sales${toQS(filters)}`)
}

export function getSupportReport(filters: ReportFilters = {}): Promise<SupportReportResponse> {
  return request(`${BASE}/reports/support${toQS(filters)}`)
}

export function getContractReport(filters: ContractFilters = {}): Promise<ContractReportResponse> {
  return request(`${BASE}/reports/contracts${toQS(filters)}`)
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function exportReport(url: string, filename: string): Promise<void> {
  const resp = await fetch(url, { credentials: 'include' })
  if (!resp.ok) throw new Error('Export failed')
  const blob = await resp.blob()
  triggerDownload(blob, filename)
}

export const exportSalesReport = (filters: ReportFilters = {}) =>
  exportReport(`${BASE}/reports/sales/export${toQS(filters)}`, 'sales_report.csv')

export const exportSupportReport = (filters: ReportFilters = {}) =>
  exportReport(`${BASE}/reports/support/export${toQS(filters)}`, 'support_report.csv')

export const exportContractReport = (filters: ContractFilters = {}) =>
  exportReport(`${BASE}/reports/contracts/export${toQS(filters)}`, 'contracts_report.csv')
