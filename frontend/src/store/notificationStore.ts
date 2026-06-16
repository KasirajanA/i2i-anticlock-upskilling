import { create } from 'zustand'
import { listContracts } from '../services/contractsApi'

interface NotificationState {
  renewalDueCount: number
  isPolling: boolean
  startPolling: (intervalMs?: number) => void
  stopPolling: () => void
  refresh: () => Promise<void>
}

let _intervalId: ReturnType<typeof setInterval> | null = null

export const useNotificationStore = create<NotificationState>((set, get) => ({
  renewalDueCount: 0,
  isPolling: false,

  async refresh() {
    try {
      const data = await listContracts({ is_renewal_due: true, limit: 1 })
      set({ renewalDueCount: data.total })
    } catch {
      // Ignore network errors during polling
    }
  },

  startPolling(intervalMs = 60_000) {
    if (get().isPolling) return
    get().refresh()
    _intervalId = setInterval(() => get().refresh(), intervalMs)
    set({ isPolling: true })
  },

  stopPolling() {
    if (_intervalId !== null) {
      clearInterval(_intervalId)
      _intervalId = null
    }
    set({ isPolling: false })
  },
}))
