import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { addComment, getComments } from '../services/dealService'

export function useComments(refId: string) {
  return useQuery({
    queryKey: ['comments', refId],
    queryFn: () => getComments(refId),
    enabled: Boolean(refId),
  })
}

export function useAddComment(refId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: string) => addComment(refId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['comments', refId] })
    },
  })
}
