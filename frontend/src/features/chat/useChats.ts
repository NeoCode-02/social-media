import { useQuery } from '@tanstack/react-query'

import { listChats } from '@/api/chats'

export function useChats() {
  return useQuery({
    queryKey: ['chats'],
    queryFn: async () => (await listChats()).data,
  })
}
