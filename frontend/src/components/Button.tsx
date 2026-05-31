import type { ComponentProps } from 'react'

import { cn } from '@/lib/utils'

type Variant = 'primary' | 'ghost' | 'subtle' | 'danger'

interface ButtonProps extends ComponentProps<'button'> {
  variant?: Variant
  loading?: boolean
}

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-accent text-accentink hover:brightness-105 shadow-soft',
  ghost: 'bg-transparent text-muted hover:text-text hover:bg-cardhover',
  subtle: 'bg-card text-text hover:bg-cardhover border border-border',
  danger: 'bg-danger/15 text-danger hover:bg-danger/25',
}

export function Button({
  variant = 'primary',
  loading,
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60',
        VARIANTS[variant],
        className,
      )}
      {...rest}
    >
      {loading && (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  )
}
