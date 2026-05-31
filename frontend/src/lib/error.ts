export function apiError(e: unknown): string {
  const ax = e as { response?: { data?: { detail?: unknown } } }
  const detail = ax?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
  return 'Something went wrong. Please try again.'
}
