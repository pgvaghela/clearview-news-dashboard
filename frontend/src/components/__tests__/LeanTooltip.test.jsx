import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import LeanTooltip from '../LeanTooltip.jsx'

const PROPS = {
  whyLabel: 'Rated Left by AllSides blind surveys.',
  ratingProvider: 'AllSides',
  ratingMethod: 'Blind surveys',
  confidence: 'Community consensus',
}

describe('LeanTooltip', () => {
  it('renders the Why this label? button', () => {
    render(<LeanTooltip {...PROPS} />)
    expect(screen.getByRole('button', { name: /why this label/i })).toBeInTheDocument()
  })

  it('panel is hidden by default', () => {
    render(<LeanTooltip {...PROPS} />)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('clicking the button shows the panel with provider, method, confidence', () => {
    render(<LeanTooltip {...PROPS} />)
    fireEvent.click(screen.getByRole('button', { name: /why this label/i }))
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    expect(screen.getByText('AllSides')).toBeInTheDocument()
    expect(screen.getByText('Blind surveys')).toBeInTheDocument()
    expect(screen.getByText('Community consensus')).toBeInTheDocument()
    expect(screen.getByText(PROPS.whyLabel)).toBeInTheDocument()
  })

  it('clicking close hides the panel', () => {
    render(<LeanTooltip {...PROPS} />)
    fireEvent.click(screen.getByRole('button', { name: /why this label/i }))
    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('renders nothing when whyLabel is absent', () => {
    const { container } = render(<LeanTooltip whyLabel={null} />)
    expect(container).toBeEmptyDOMElement()
  })
})
