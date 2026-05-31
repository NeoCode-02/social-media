import { useQuery } from '@tanstack/react-query'

import { getHealth } from '@/api/health'

export function HomePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
  })

  const backend = isLoading
    ? 'checking…'
    : isError
      ? 'unreachable'
      : (data?.status ?? 'unknown')

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 bg-neutral-950 text-neutral-100">
      <h1 className="text-4xl font-semibold tracking-tight">social-media</h1>
      <p className="text-neutral-400">Realtime chat + social platform</p>
      <span
        className="rounded-full border border-neutral-700 px-3 py-1 text-sm"
        data-testid="backend-status"
      >
        backend: {backend}
      </span>
    </div>
  )
}
