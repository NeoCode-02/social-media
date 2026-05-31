import { motion } from 'framer-motion'
import { Download, X } from 'lucide-react'
import { useEffect } from 'react'

interface Props {
  src: string
  name: string
  onClose: () => void
  onDownload?: () => void
}

export function Lightbox({ src, name, onClose, onDownload }: Props) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 z-[60] flex flex-col bg-black/85 backdrop-blur-sm"
    >
      <div
        className="flex items-center justify-between px-5 py-4"
        onClick={(e) => e.stopPropagation()}
      >
        <span className="truncate text-sm font-medium text-white/80">{name}</span>
        <div className="flex items-center gap-1">
          {onDownload && (
            <button
              onClick={onDownload}
              title="Download"
              className="flex h-10 w-10 items-center justify-center rounded-full text-white/80 transition hover:bg-white/10 hover:text-white"
            >
              <Download size={20} />
            </button>
          )}
          <button
            onClick={onClose}
            title="Close"
            className="flex h-10 w-10 items-center justify-center rounded-full text-white/80 transition hover:bg-white/10 hover:text-white"
          >
            <X size={22} />
          </button>
        </div>
      </div>
      <div className="flex min-h-0 flex-1 items-center justify-center p-4">
        <motion.img
          key={src}
          initial={{ scale: 0.92, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          src={src}
          alt={name}
          onClick={(e) => e.stopPropagation()}
          className="max-h-full max-w-full rounded-lg object-contain shadow-2xl"
        />
      </div>
    </motion.div>
  )
}
