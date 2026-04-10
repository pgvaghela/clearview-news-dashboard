import { useState } from 'react'
import { useApi } from '../hooks/useApi.js'
import { fetchStories } from '../services/api.js'
import StoryCard from '../components/StoryCard.jsx'
import './Dashboard.css'

export default function Dashboard() {
  const [page, setPage] = useState(1)

  const { data, loading, error } = useApi(
    () => fetchStories(page),
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
