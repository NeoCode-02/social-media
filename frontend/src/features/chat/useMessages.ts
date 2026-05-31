import { useReducer, useState } from 'react'

import { useQuery, useQueryClient } from '@tanstack/react-query'

import { listMessages } from '@/api/chats'
import type { Message } from '@/api/types'

// Chats whose full history has been loaded (module scope: survives remounts).
const endedChats = new Set<string>()

/** Loads a chat's messages (chronological) with "load older" pagination. */
export function useMessages(chatId: string) {
  const qc = useQueryClient()
  const [loadingOlder, setLoadingOlder] = useState(false)
  const [, bump] = useReducer((n: number) => n + 1, 0)

  const query = useQuery({
    queryKey: ['messages', chatId],
    queryFn: async () => {
      const { data } = await listMessages(chatId)
      return data.messages.slice().reverse() // newest-first → chronological
    },
  })

  const loadOlder = async () => {
    const current = qc.getQueryData<Message[]>(['messages', chatId])
    if (!current || current.length === 0 || loadingOlder || endedChats.has(chatId)) return
    setLoadingOlder(true)
    try {
      const { data } = await listMessages(chatId, current[0].id)
      const older = data.messages.slice().reverse()
      if (older.length === 0) {
        endedChats.add(chatId)
        bump()
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
    hasMore: !endedChats.has(chatId),
  }
}
