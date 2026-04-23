import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import StoryCard from '../StoryCard.jsx'

const STORY = {
  id: 1,
  headline: 'Senate passes major infrastructure bill',
  first_seen_at: new Date(Date.now() - 120 * 60000).toISOString(),
  last_updated_at: new Date(Date.now() - 20 * 60000).toISOString(),
  article_count: 3,
  lean_categories_present: 'left,center,right',
  preview_articles: [
    { id: 1, title: 'A', url: '#', outlet_name: 'NPR',     lean_display: 'Left'   },
    { id: 2, title: 'B', url: '#', outlet_name: 'Reuters', lean_display: 'Center' },
    { id: 3, title: 'C', url: '#', outlet_name: 'Fox News',lean_display: 'Right'  },
  ],
}

describe('StoryCard', () => {
  const wrap = (story = STORY) =>
    render(<MemoryRouter><StoryCard story={story} /></MemoryRouter>)

  it('renders the story headline', () => {
    wrap()
    expect(screen.getByText('Senate passes major infrastructure bill')).toBeInTheDocument()
  })

  it('renders the source count', () => {
    wrap()
    expect(screen.getByText('3 sources')).toBeInTheDocument()
  })

  it('renders a LeanBadge for each preview article', () => {
    wrap()
    expect(screen.getByText('Left')).toBeInTheDocument()
    expect(screen.getByText('Center')).toBeInTheDocument()
    expect(screen.getByText('Right')).toBeInTheDocument()
  })

  it('renders outlet names', () => {
    wrap()
    expect(screen.getByText('NPR')).toBeInTheDocument()
    expect(screen.getByText('Reuters')).toBeInTheDocument()
    expect(screen.getByText('Fox News')).toBeInTheDocument()
  })

  it('shows Fact checked when has_fact_checks is true', () => {
    wrap({ ...STORY, has_fact_checks: true })
    expect(screen.getByText('Fact checked')).toBeInTheDocument()
  })

  it('does not show Fact checked when has_fact_checks is false', () => {
    wrap({ ...STORY, has_fact_checks: false })
    expect(screen.queryByText('Fact checked')).not.toBeInTheDocument()
  })

  it('shows Sources when has_webcite is true', () => {
    wrap({ ...STORY, has_webcite: true })
    expect(screen.getByText('Sources')).toBeInTheDocument()
  })
})
