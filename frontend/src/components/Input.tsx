import { forwardRef, type ComponentProps } from 'react'

import { cn } from '@/lib/utils'

interface InputProps extends ComponentProps<'input'> {
  label?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, className, id, ...rest },
  ref,
) {
  return (
    <label className="block">
      {label && <span className="mb-1.5 block text-xs font-medium text-muted">{label}</span>}
      <input
        ref={ref}
        id={id}
        className={cn(
          'w-full rounded-xl border border-border bg-card px-4 py-3 text-sm text-text placeholder:text-faint',
          'transition focus:border-violet/60 focus:outline-none focus:ring-2 focus:ring-violet/30',
          className,
        )}
        {...rest}
      />
      {hint && <span className="mt-1 block text-xs text-faint">{hint}</span>}
    </label>
  )
})
