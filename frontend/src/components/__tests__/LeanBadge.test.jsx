import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import LeanBadge from '../LeanBadge.jsx'

describe('LeanBadge', () => {
  it('renders the lean label text', () => {
    render(<LeanBadge lean="Left" />)
    expect(screen.getByText('Left')).toBeInTheDocument()
  })

  it('renders Center', () => {
    render(<LeanBadge lean="Center" />)
    expect(screen.getByText('Center')).toBeInTheDocument()
  })

  it('renders Right', () => {
    render(<LeanBadge lean="Right" />)
    expect(screen.getByText('Right')).toBeInTheDocument()
  })

  it('renders nothing for Unknown', () => {
    const { container } = render(<LeanBadge lean="Unknown" />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when lean is null', () => {
    const { container } = render(<LeanBadge lean={null} />)
    expect(container).toBeEmptyDOMElement()
  })
})
