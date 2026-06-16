import type { Role } from './types/auth'

export const MODULE_PERMISSIONS: Record<string, Role[]> = {
  contacts: ['Admin', 'Manager', 'Sales Rep', 'Support Agent'],
  sales_pipeline: ['Admin', 'Manager', 'Sales Rep'],
  contracts: ['Admin', 'Manager', 'Sales Rep'],
  customer_support: ['Admin', 'Manager', 'Support Agent'],
  analytics: ['Admin', 'Manager', 'Sales Rep', 'Support Agent'],
  user_team_management: ['Admin'],
}

export const MODULE_WRITE_PERMISSIONS: Record<string, Role[]> = {
  contacts: ['Admin', 'Manager', 'Sales Rep'],
  sales_pipeline: ['Admin', 'Manager', 'Sales Rep'],
  contracts: ['Admin', 'Manager', 'Sales Rep'],
  customer_support: ['Admin', 'Manager', 'Support Agent'],
  analytics: ['Admin', 'Manager'],
  user_team_management: ['Admin'],
}

export function canAccess(role: Role | undefined, module: string, write = false): boolean {
  if (!role) return false
  const matrix = write ? MODULE_WRITE_PERMISSIONS : MODULE_PERMISSIONS
  return (matrix[module] ?? []).includes(role)
}
