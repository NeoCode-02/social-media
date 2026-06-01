import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-center">
          <div className="rounded-2xl border border-border bg-card p-8 shadow-xl max-w-md">
            <h1 className="mb-4 text-2xl font-bold text-destructive">Something went wrong</h1>
            <p className="mb-6 text-faint">
              An unexpected error occurred. Please try refreshing the page.
            </p>
            <div className="mb-6 overflow-auto rounded bg-background p-4 text-left text-xs text-faint border border-border max-h-32">
              {this.state.error?.message || 'Unknown Error'}
            </div>
            <button
              onClick={() => window.location.reload()}
              className="rounded-full bg-accent px-6 py-2.5 font-medium text-white transition hover:bg-accent/90"
            >
              Refresh Page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
