import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useApi } from '../hooks/useApi.js'
import { fetchStories } from '../services/api.js'
import StoryCard from '../components/StoryCard.jsx'
import LeanBadge from '../components/LeanBadge.jsx'
import './Dashboard.css'

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 60000)
  if (diff < 1) return 'Just now'
  if (diff < 60) return `${diff}m ago`
  if (diff < 1440) return `${Math.floor(diff / 60)}h ago`
  return `${Math.floor(diff / 1440)}d ago`
}

function getFirstImage(story) {
  const articles = story.preview_articles || []
  for (const a of articles) {
    if (a.image_url) return a.image_url
  }
  return null
}

function FeaturedStory({ story }) {
  const navigate = useNavigate()
  const previews = story.preview_articles || []
  const heroImage = getFirstImage(story)

  return (
    <motion.div
      className="featured-story"
      onClick={() => navigate(`/story/${story.id}`)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -2 }}
    >
      {heroImage && (
        <div className="featured-story__image-wrap">
          <img
            src={heroImage}
            alt=""
            className="featured-story__image"
            onError={e => { e.currentTarget.parentElement.style.display = 'none' }}
          />
          <div className="featured-story__image-overlay" />
        </div>
      )}

      <div className="featured-story__body">
        <div className="featured-story__eyebrow">
          <span className="featured-story__label">Top Story</span>
          <div className="featured-story__badges">
            {previews.slice(0, 4).map(a => (
              <LeanBadge key={a.id} lean={a.lean_display} />
            ))}
          </div>
        </div>

        <h2 className="featured-story__headline">{story.headline}</h2>

        {previews.length > 0 && (
          <ul className="featured-story__sources">
            {previews.slice(0, 3).map(a => (
              <li key={a.id} className="featured-story__source-item">
                <span className="featured-story__source-outlet">{a.outlet_name}</span>
                <span className="featured-story__source-title">{a.title}</span>
              </li>
            ))}
          </ul>
        )}

        <div className="featured-story__meta">
          <span>{story.article_count} sources</span>
          <span className="featured-story__dot" />
          <span>{timeAgo(story.last_updated_at)}</span>
          {story.has_fact_checks && (
            <span className="featured-story__fc-badge">✓ Fact checked</span>
          )}
          {story.has_webcite && (
            <span className="featured-story__wc-badge">Sources cited</span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function SidebarStory({ story, index }) {
  const navigate = useNavigate()
  const image = getFirstImage(story)

  return (
    <motion.div
      className="sidebar-story"
      onClick={() => navigate(`/story/${story.id}`)}
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: 0.12 + index * 0.08, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="sidebar-story__text">
        <div className="sidebar-story__badges">
          {(story.preview_articles || []).slice(0, 2).map(a => (
            <LeanBadge key={a.id} lean={a.lean_display} />
          ))}
        </div>
        <div className="sidebar-story__headline">{story.headline}</div>
        <div className="sidebar-story__meta">
          <span>{story.article_count} sources</span>
          <span className="sidebar-story__dot" />
          <span>{timeAgo(story.last_updated_at)}</span>
          {story.has_fact_checks && <span className="sidebar-story__fc">✓ FC</span>}
        </div>
      </div>
      {image && (
        <div className="sidebar-story__thumb-wrap">
          <img
            src={image}
            alt=""
            className="sidebar-story__thumb"
            onError={e => { e.currentTarget.parentElement.style.display = 'none' }}
          />
        </div>
      )}
    </motion.div>
  )
}

export default function Dashboard() {
  const [page, setPage] = useState(1)
  const { data, loading, error } = useApi(() => fetchStories(page), [page])

  const stories = data?.stories || []
  const featured = stories[0]
  const sidebar  = stories.slice(1, 4)
  const grid     = stories.slice(4)

  return (
    <div className="dashboard">
      {/* ── Header ── */}
      <motion.header
        className="dashboard__header"
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="dashboard__header-inner">
          <div className="dashboard__logo">
            <span className="logo-clear">Clear</span><span className="logo-view">View</span>
          </div>
          <p className="dashboard__tagline">
            Every story. Every perspective. Fact-checked.
          </p>
          {data && (
            <div className="dashboard__count-pill">{data.total} stories tracked</div>
          )}
        </div>
      </motion.header>

      <div className="dashboard__section-rule">
        <div className="dashboard__section-rule-inner">
          <span className="dashboard__section-rule-label">Top Stories</span>
          <span className="dashboard__section-rule-date">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </span>
        </div>
      </div>

      <main className="dashboard__main">
        <AnimatePresence mode="wait">
          {loading && (
            <motion.div key="loading" className="dashboard__state"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="dashboard__spinner" />
              Loading stories…
            </motion.div>
          )}

          {error && (
            <motion.div key="error" className="dashboard__state dashboard__state--error"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              Could not load stories. {error}
            </motion.div>
          )}

          {data && !loading && (
            <motion.div key={`page-${page}`}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}>

              {/* ── Hero section ── */}
              {featured && (
                <section className="dashboard__hero">
                  <div className="dashboard__hero-featured">
                    <FeaturedStory story={featured} />
                  </div>
                  <aside className="dashboard__hero-sidebar">
                    <div className="dashboard__sidebar-label">More Stories</div>
                    {sidebar.map((s, i) => (
                      <SidebarStory key={s.id} story={s} index={i} />
                    ))}
                  </aside>
                </section>
              )}

              {/* ── Grid ── */}
              {grid.length > 0 && (
                <section className="dashboard__grid-section">
                  <div className="dashboard__grid-header">
                    <h2 className="dashboard__grid-title">Trending</h2>
                    <span className="dashboard__grid-count">{data.total} stories</span>
                  </div>
                  <div className="story-grid">
                    {grid.map((story, i) => (
                      <StoryCard key={story.id} story={story} index={i} />
                    ))}
                  </div>
                </section>
              )}

              {/* ── Pagination ── */}
              {data.total > data.page_size && (
                <motion.div className="dashboard__pagination"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }}>
                  <motion.button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                    className="pagination-btn" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
                    ← Previous
                  </motion.button>
                  <span className="pagination-info">Page {page}</span>
                  <motion.button disabled={data.stories.length < data.page_size}
                    onClick={() => setPage(p => p + 1)} className="pagination-btn"
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
                    Next →
                  </motion.button>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
