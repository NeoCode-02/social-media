import { useState } from 'react'

import { useQuery, useQueryClient } from '@tanstack/react-query'

import { listMessages } from '@/api/chats'
import type { Message } from '@/api/types'

/** Loads a chat's messages (chronological) with "load older" pagination. */
export function useMessages(chatId: string) {
  const qc = useQueryClient()
  const [loadingOlder, setLoadingOlder] = useState(false)
  // "Reached the start of history" is per-conversation-view session state,
  // not server-cached data. Local useState is the right home.
  const [ended, setEnded] = useState(false)

  const query = useQuery({
    queryKey: ['messages', chatId],
    queryFn: async () => {
      const { data } = await listMessages(chatId)
      return data.messages.slice().reverse() // newest-first → chronological
    },
  })

  const loadOlder = async () => {
    const current = qc.getQueryData<Message[]>(['messages', chatId])
    if (!current || current.length === 0 || loadingOlder || ended) return
    setLoadingOlder(true)
    try {
      const { data } = await listMessages(chatId, current[0].id)
      const older = data.messages.slice().reverse()
      if (older.length === 0) {
        setEnded(true)
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
