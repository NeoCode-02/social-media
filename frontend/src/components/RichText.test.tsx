import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

vi.mock('@/api/users', () => ({
  getUserByUsername: vi.fn(),
}))

import { RichText } from './RichText'

function renderRich(text: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <RichText text={text} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('RichText', () => {
  it('renders plain text as-is (escapes safely)', () => {
    renderRich('hello <script>alert(1)</script>')
    // The literal <script> must be present in the DOM as TEXT, never as
    // an executable element.
    expect(document.body.querySelector('script')).toBeNull()
    expect(screen.getByText(/hello <script>/)).toBeInTheDocument()
  })

  it('renders hashtags as links to /tag/:tag (lowercased)', () => {
    renderRich('loving #FOO')
    const link = screen.getByRole('link', { name: '#FOO' })
    expect(link).toHaveAttribute('href', '/tag/foo')
  })

  it('renders URLs with target=_blank and break-all', () => {
    renderRich('see https://example.com/foo')
    const link = screen.getByRole('link', { name: 'https://example.com/foo' })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noreferrer')
    expect(link.className).toMatch(/break-all/)
  })
})
