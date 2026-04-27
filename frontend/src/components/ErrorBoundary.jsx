import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '3rem 2rem',
          textAlign: 'center',
          color: 'var(--color-text-muted)',
          fontFamily: 'var(--font-sans)',
        }}>
          <h2 style={{ marginBottom: '0.5rem', color: 'var(--color-text)' }}>
            Something went wrong
          </h2>
          <p>Try refreshing the page.</p>
        </div>
      )
    }
    return this.props.children
  }
}
