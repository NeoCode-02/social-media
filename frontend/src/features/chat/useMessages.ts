import { useState } from 'react'

import { useQuery, useQueryClient } from '@tanstack/react-query'

import { listMessages } from '@/api/chats'
import type { Message } from '@/api/types'

/** Loads a chat's messages (chronological) with "load older" pagination. */
export function useMessages(chatId: string) {
  const qc = useQueryClient()
  const [loadingOlder, setLoadingOlder] = useState(false)

  const query = useQuery({
    queryKey: ['messages', chatId],
    queryFn: async () => {
      const { data } = await listMessages(chatId)
      return data.messages.slice().reverse() // newest-first → chronological
    },
  })

  // "Reached the start of history" flag lives in the cache (not module scope):
  // survives remounts but is cleared on logout via qc.clear().
  const { data: ended = false } = useQuery<boolean>({
    queryKey: ['messages', chatId, 'ended'],
    queryFn: () => false,
    enabled: false,
    initialData: false,
  })

  const loadOlder = async () => {
    const current = qc.getQueryData<Message[]>(['messages', chatId])
    if (!current || current.length === 0 || loadingOlder || ended) return
    setLoadingOlder(true)
    try {
      const { data } = await listMessages(chatId, current[0].id)
      const older = data.messages.slice().reverse()
      if (older.length === 0) {
        qc.setQueryData<boolean>(['messages', chatId, 'ended'], true)
      } else {
        qc.setQueryData<Message[]>(['messages', chatId], [...older, ...current])
      }
    } finally {
      setLoadingOlder(false)
    }
  }

  return {
    messages: query.data ?? [],
    isLoading: query.isLoading,
    loadOlder,
    loadingOlder,
    hasMore: !ended,
  }
}
