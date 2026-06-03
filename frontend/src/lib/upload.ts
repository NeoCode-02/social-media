import { uploadAttachment } from '@/api/chats'
import { uploadPostAttachment } from '@/api/posts'
import type { Attachment } from '@/api/types'

export type UploadScope = 'post' | 'chat'

export interface UploadOptions {
  scope: UploadScope
  /** Required when scope === 'chat'. */
  chatId?: string
  /** Max bytes; default 100MB. Callers can pass a tighter cap. */
  maxBytes?: number
  /** Max items in a single batch. */
  maxItems?: number
  /** Backend-side flags. */
  asFile?: boolean
  isVoice?: boolean
  durationMs?: number
}

const DEFAULT_MAX_BYTES = 100 * 1024 * 1024

export type UploadErrorCode = 'too_large' | 'too_many' | 'missing_chat_id' | 'unknown'

export class UploadError extends Error {
  readonly code: UploadErrorCode
  constructor(message: string, code: UploadErrorCode) {
    super(message)
    this.name = 'UploadError'
    this.code = code
  }
}

/**
 * Upload a single file in the right scope. Returns the server-issued
 * attachment metadata. Use `uploadMany` to upload a batch with cap
 * enforcement.
 */
export async function uploadFile(file: File, options: UploadOptions): Promise<Attachment> {
  const max = options.maxBytes ?? DEFAULT_MAX_BYTES
  if (file.size > max) {
    throw new UploadError(
      `"${file.name}" is too large (max ${Math.round(max / (1024 * 1024))}MB)`,
      'too_large',
    )
  }
  if (options.scope === 'chat' && !options.chatId) {
    throw new UploadError('chatId is required for chat uploads', 'missing_chat_id')
  }
  const meta = {
    asFile: options.asFile,
    isVoice: options.isVoice,
    durationMs: options.durationMs,
  }
  if (options.scope === 'post') {
    const { data } = await uploadPostAttachment(file, meta)
    return data
  }
  const { data } = await uploadAttachment(options.chatId!, file, meta)
  return data
}

/**
 * Upload a batch of files sequentially with a hard cap. Stops on the
 * first cap violation so the UI can show a clear error.
 */
export async function uploadMany(
  files: File[],
  options: UploadOptions,
): Promise<Attachment[]> {
  const cap = options.maxItems ?? (options.scope === 'post' ? 4 : 1)
  if (files.length > cap) {
    throw new UploadError(
      `You can attach up to ${cap} items per ${options.scope === 'post' ? 'post' : 'message'}.`,
      'too_many',
    )
  }
  const out: Attachment[] = []
  for (const f of files) {
    out.push(await uploadFile(f, options))
  }
  return out
}
