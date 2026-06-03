import { ImageIcon, Loader2 } from 'lucide-react'
import { useRef, useState } from 'react'

import { apiError } from '@/lib/error'

export type UploadResult<T> = { ok: T; err?: never } | { ok?: never; err: string }

interface Props {
  /** Whether more items can still be added. */
  disabled: boolean
  /** True while a file is in flight; disables the trigger. */
  uploading: boolean
  /** Called with the picked file. Throw or return a string to surface an error. */
  onPick: (file: File) => Promise<void> | void
  /** The input accept list. */
  accept?: string
  /** Visible label/title for accessibility. */
  title?: string
}

/**
 * Shared "add a file" trigger. Encapsulates the hidden <input type=file>
 * + reset-after-pick pattern so consumers don't reinvent it.
 */
export function AttachmentPicker({
  disabled,
  uploading,
  onPick,
  accept = 'image/*,video/*',
  title = 'Add photo or video',
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [err, setErr] = useState('')

  async function handle(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setErr('')
    try {
      await onPick(file)
    } catch (caught) {
      setErr(apiError(caught))
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => fileRef.current?.click()}
        disabled={disabled || uploading}
        className="flex h-9 w-9 items-center justify-center rounded-full text-accent transition hover:bg-accent/10 disabled:opacity-40"
        title={title}
      >
        {uploading ? <Loader2 size={18} className="animate-spin" /> : <ImageIcon size={18} />}
      </button>
      <input
        ref={fileRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={handle}
      />
      {err && <span className="text-xs text-danger">{err}</span>}
    </>
  )
}
