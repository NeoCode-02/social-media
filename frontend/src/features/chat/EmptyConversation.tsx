import { MessagesSquare } from 'lucide-react'

export function EmptyConversation() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-card text-faint">
        <MessagesSquare size={28} />
      </div>
      <h2 className="text-lg font-semibold">Your messages</h2>
      <p className="max-w-xs text-sm text-muted">
        Select a conversation from the left, or start a new one to begin chatting.
      </p>
    </div>
  )
}
