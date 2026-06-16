import { useQuery } from '@tanstack/react-query'
import {
  getContractReport,
  getDashboard,
  getSalesReport,
  getSupportReport,
} from '../services/analyticsApi'
import type { ContractFilters, ReportFilters } from '../types/analytics'

export const REPORT_STALE_TIME = 4 * 60 * 1000
export const SUPPORT_STALE_TIME = 50 * 1000
export const GC_TIME = 10 * 60 * 1000

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
    staleTime: 0,
    gcTime: GC_TIME,
  })
}

export function useSalesReport(filters: ReportFilters = {}) {
  return useQuery({
    queryKey: ['report', 'sales', filters],
    queryFn: () => getSalesReport(filters),
    staleTime: REPORT_STALE_TIME,
    gcTime: GC_TIME,
  })
}

export function useSupportReport(filters: ReportFilters = {}) {
  return useQuery({
    queryKey: ['report', 'support', filters],
    queryFn: () => getSupportReport(filters),
    staleTime: SUPPORT_STALE_TIME,
    gcTime: GC_TIME,
  })
}

export function useContractReport(filters: ContractFilters = {}) {
  return useQuery({
    queryKey: ['report', 'contracts', filters],
    queryFn: () => getContractReport(filters),
    staleTime: REPORT_STALE_TIME,
    gcTime: GC_TIME,
  })
}
