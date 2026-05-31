export function FullScreenLoader({ label }: { label?: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 text-muted">
      <span className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
      {label && <span className="text-sm">{label}</span>}
    </div>
  )
}
