import { useState } from 'react'
import { useApi } from '../hooks/useApi.js'
import { fetchStories } from '../services/api.js'
import StoryCard from '../components/StoryCard.jsx'
import './Dashboard.css'

// ── Mock data — used until API wiring is complete (Sprint 1) ──────────────
const MOCK_STORIES = {
  total: 10,
  page: 1,
  page_size: 15,
  stories: Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    headline: [
      'Senate passes major infrastructure bill after weeks of debate',
      'Federal Reserve holds interest rates steady, signals caution',
      'Supreme Court takes up landmark social media free speech case',
      'NASA announces new Moon mission timeline pushed to 2027',
      'Tech layoffs continue as AI reshapes hiring across Silicon Valley',
      'Border policy overhaul faces legal challenges in three states',
      'Ukraine aid package clears House in bipartisan vote',
      'FDA approves new Alzheimer\'s drug after years of trials',
      'Midwest flooding displaces thousands as rivers overflow banks',
      'China trade tensions escalate over semiconductor export controls',
    ][i],
    first_seen_at: new Date(Date.now() - (i + 1) * 38 * 60000).toISOString(),
    last_updated_at: new Date(Date.now() - i * 12 * 60000).toISOString(),
    article_count: 3 + (i % 4),
    lean_categories_present: 'left,center,right',
    preview_articles: [
      {
        id: i * 3 + 1, title: 'Article A', url: '#',
        outlet_name: ['NPR', 'MSNBC', 'HuffPost'][i % 3],
        lean_display: 'Left',
      },
      {
        id: i * 3 + 2, title: 'Article B', url: '#',
        outlet_name: ['Reuters', 'AP', 'BBC News'][i % 3],
        lean_display: 'Center',
      },
      {
        id: i * 3 + 3, title: 'Article C', url: '#',
        outlet_name: ['Fox News', 'Breitbart', 'Daily Wire'][i % 3],
        lean_display: 'Right',
      },
    ],
  })),
}

const USE_MOCK = true  // flip to false once API wiring is complete

export default function Dashboard() {
  const [page, setPage] = useState(1)

  const { data, loading, error } = useApi(
    () => USE_MOCK ? Promise.resolve(MOCK_STORIES) : fetchStories(page),
    [page]
  )

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div className="dashboard__header-inner">
          <h1 className="dashboard__logo">
            <span className="logo-clear">Clear</span>
            <span className="logo-view">View</span>
          </h1>
          <p className="dashboard__tagline">
            Understand what happened, how it&apos;s framed, and what&apos;s verified — fast.
          </p>
        </div>
      </header>

      <main className="dashboard__main">
        <div className="dashboard__section-label">
          Trending Now
          {data && <span className="dashboard__count">{data.total} stories</span>}
        </div>

        {loading && (
          <div className="dashboard__state">Loading stories…</div>
        )}

        {error && (
          <div className="dashboard__state dashboard__state--error">
            Could not load stories. {error}
          </div>
        )}

        {data && !loading && (
          <>
            <div className="story-grid">
              {data.stories.map(story => (
                <StoryCard key={story.id} story={story} />
              ))}
            </div>

            {data.total > data.page_size && (
              <div className="dashboard__pagination">
                <button
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                  className="pagination-btn"
                >
                  ← Previous
                </button>
                <span className="pagination-info">Page {page}</span>
                <button
                  disabled={data.stories.length < data.page_size}
                  onClick={() => setPage(p => p + 1)}
                  className="pagination-btn"
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
