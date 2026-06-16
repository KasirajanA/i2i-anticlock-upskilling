import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from '@tanstack/react-query'
import {
  createContract,
  deleteAttachment,
  getActivityLog,
  getContract,
  listContracts,
  renewContract,
  transitionContract,
  updateContract,
  uploadAttachment,
} from '../services/contractsApi'
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

export function useContracts(
  filters: ContractFilterParams = {},
): UseQueryResult<ContractListResponse> {
  return useQuery({
    queryKey: ['contracts', filters],
    queryFn: () => listContracts(filters),
  })
}

export function useContract(refId: string): UseQueryResult<Contract> {
  return useQuery({
    queryKey: ['contract', refId],
    queryFn: () => getContract(refId),
    enabled: Boolean(refId),
  })
}

export function useActivityLog(refId: string): UseQueryResult<ActivityLogResponse> {
  return useQuery({
    queryKey: ['contract-activity', refId],
    queryFn: () => getActivityLog(refId),
    enabled: Boolean(refId),
  })
}

export function useMutateContract() {
  const qc = useQueryClient()

  const createMutation = useMutation<Contract, Error, ContractCreateRequest>({
    mutationFn: createContract,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contracts'] }),
  })

  const updateMutation = useMutation<
    Contract,
    Error,
    { refId: string; payload: ContractUpdateRequest }
  >({
    mutationFn: ({ refId, payload }) => updateContract(refId, payload),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['contracts'] })
      qc.invalidateQueries({ queryKey: ['contract', data.ref_id] })
    },
  })

  return { createMutation, updateMutation }
}

export function useTransitionContract(refId: string) {
  const qc = useQueryClient()
  return useMutation<TransitionResponse, Error, TransitionRequest>({
    mutationFn: (payload) => transitionContract(refId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contract', refId] })
      qc.invalidateQueries({ queryKey: ['contract-activity', refId] })
      qc.invalidateQueries({ queryKey: ['contracts'] })
    },
  })
}

export function useRenewContract(refId: string) {
  const qc = useQueryClient()
  return useMutation<RenewResponse, Error, void>({
    mutationFn: () => renewContract(refId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contracts'] })
      qc.invalidateQueries({ queryKey: ['contract', refId] })
    },
  })
}

export function useAttachmentMutation(refId: string) {
  const qc = useQueryClient()

  const upload = useMutation<unknown, Error, File>({
    mutationFn: (file) => uploadAttachment(refId, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contract', refId] }),
  })

  const remove = useMutation<void, Error, void>({
    mutationFn: () => deleteAttachment(refId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contract', refId] }),
  })

  return { upload, remove }
}
