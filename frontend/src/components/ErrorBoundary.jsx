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
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'Georgia, serif',
          textAlign: 'center',
          padding: '32px',
          gap: '12px',
        }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#121212' }}>
            ClearView
          </div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, color: '#121212' }}>
            Something went wrong
          </h1>
          <p style={{ fontSize: '0.88rem', color: '#666', margin: 0 }}>
            Reload the page to continue.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '8px', padding: '8px 24px',
              background: '#000', color: '#fff', border: 'none',
              cursor: 'pointer', fontSize: '0.72rem', fontWeight: 700,
              letterSpacing: '0.08em', textTransform: 'uppercase',
              fontFamily: 'Arial, sans-serif',
            }}
          >
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
