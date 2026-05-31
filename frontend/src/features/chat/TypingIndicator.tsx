import { motion } from 'framer-motion'

export function TypingIndicator({ label }: { label?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-2 px-1"
    >
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-card px-3.5 py-3">
        <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted" />
        <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted" />
        <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted" />
      </div>
      {label && <span className="text-xs text-faint">{label}</span>}
    </motion.div>
  )
}
