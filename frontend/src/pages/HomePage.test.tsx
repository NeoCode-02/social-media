import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { HomePage } from './HomePage'

describe('HomePage', () => {
  it('renders the app title', () => {
    const qc = new QueryClient()
    render(
      <QueryClientProvider client={qc}>
        <HomePage />
      </QueryClientProvider>,
    )
    expect(
      screen.getByRole('heading', { name: 'social-media' }),
    ).toBeInTheDocument()
  })
})
