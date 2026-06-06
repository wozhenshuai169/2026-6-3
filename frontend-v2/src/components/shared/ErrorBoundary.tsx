import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode; fallback?: ReactNode }
interface State { hasError: boolean; error?: Error }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex flex-col items-center justify-center h-full gap-4 px-8 text-center">
          <span className="text-5xl">😿</span>
          <h2 className="text-lg font-semibold">页面加载异常</h2>
          <p className="text-text-secondary text-sm">{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="px-6 py-2 rounded-xl bg-primary/20 text-primary-light text-sm"
          >
            重试
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
