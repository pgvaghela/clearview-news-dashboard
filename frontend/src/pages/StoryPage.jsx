import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useApi } from '../hooks/useApi.js'
import { fetchStory } from '../services/api.js'
import LeanBadge from '../components/LeanBadge.jsx'
import LeanTooltip from '../components/LeanTooltip.jsx'
import StoryFactSources from '../components/StoryFactSources.jsx'
import './StoryPage.css'

const LEAN_COLUMNS = [
  { key: 'left',       label: 'Left',       colorVar: 'var(--color-left)' },
  { key: 'lean_left',  label: 'Lean Left',  colorVar: 'var(--color-lean-left)' },
  { key: 'center',     label: 'Center',     colorVar: 'var(--color-center)' },
  { key: 'lean_right', label: 'Lean Right', colorVar: 'var(--color-lean-right)' },
  { key: 'right',      label: 'Right',      colorVar: 'var(--color-right)' },
]


function ArticleItem({ article, index }) {
  return (
    <motion.div
      className="article-item"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.07, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <div className="article-item__outlet">
        <span>{article.outlet_name}</span>
        <LeanBadge lean={article.lean_display} />
      </div>
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="article-item__title"
        onClick={e => e.stopPropagation()}
      >
        {article.title}
      </a>
      {article.description && (
        <p className="article-item__desc">{article.description}</p>
      )}
      <div className="article-item__footer">
        <LeanTooltip
          whyLabel={article.why_label}
          ratingProvider={article.rating_provider}
          ratingMethod={article.rating_method}
          confidence={article.confidence}
        />
      </div>
    </motion.div>
  )
}

export default function StoryPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [activeFilter, setActiveFilter] = useState(null)

  const { data: story, loading, error } = useApi(
    () => fetchStory(id),
    [id]
  )

  const filledColumns = LEAN_COLUMNS.filter(
    col => story && (story[col.key] || []).length > 0
  )

  const visibleColumns = activeFilter
    ? filledColumns.filter(col => col.key === activeFilter)
    : filledColumns

  const timeAgo = (dateStr) => {
    if (!dateStr) return ''
    const diff = Math.floor((Date.now() - new Date(dateStr)) / 60000)
    const d = Math.max(0, diff)
    if (d < 1) return 'just now'
    if (d < 60) return `${d}m ago`
    if (d < 1440) return `${Math.floor(d / 60)}h ago`
    return `${Math.floor(d / 1440)}d ago`
  }

  return (
    <motion.div
      className="story-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.35 }}
    >
      <header className="story-page__header">
        <div className="story-page__header-inner">
          <motion.button
            className="back-btn"
            onClick={() => navigate('/')}
            whileHover={{ x: -3 }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          >
            ← ClearView
          </motion.button>

          <AnimatePresence>
            {story && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.1 }}
              >
                <h1 className="story-page__headline">{story.headline}</h1>
                <div className="story-page__meta">
                  <span>{story.article_count} sources</span>
                  <span>·</span>
                  <span>Updated {timeAgo(story.last_updated_at)}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      <main className="story-page__main">
        {loading && (
          <motion.div
            className="story-page__state"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            Loading story…
          </motion.div>
        )}

        {error && (
          <motion.div
            className="story-page__state story-page__state--error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {error}
          </motion.div>
        )}

        {story && !loading && (
          <>
            <motion.div
              className="lean-explainer"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.15 }}
            >
              <span className="lean-explainer__text">
                Coverage grouped by political lean —
              </span>
              {LEAN_COLUMNS.map(col => {
                const count = (story[col.key] || []).length
                const isActive = activeFilter === col.key
                if (count > 0) {
                  return (
                    <motion.button
                      key={col.key}
                      type="button"
                      className={`lean-explainer__chip lean-explainer__chip--link${isActive ? ' lean-explainer__chip--active' : ''}`}
                      style={{ color: col.colorVar, borderBottomWidth: isActive ? '2px' : '1px' }}
                      onClick={() => setActiveFilter(isActive ? null : col.key)}
                      whileHover={{ scale: 1.08 }}
                      whileTap={{ scale: 0.94 }}
                    >
                      {col.label}
                    </motion.button>
                  )
                }
                return (
                  <span
                    key={col.key}
                    className="lean-explainer__chip lean-explainer__chip--muted"
                    style={{ color: col.colorVar }}
                    title="No articles in this category for this story"
                  >
                    {col.label}
                  </span>
                )
              })}
            </motion.div>

            <div
              className="lean-columns"
              style={{ '--col-count': filledColumns.length || 3 }}
            >
              {visibleColumns.map((col, colIndex) => (
                <motion.section
                  key={col.key}
                  id={`story-lean-${col.key}`}
                  className="lean-column"
                  style={{ '--col-color': col.colorVar }}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.4,
                    delay: 0.2 + colIndex * 0.1,
                    ease: [0.25, 0.1, 0.25, 1],
                  }}
                >
                  <div className="lean-column__header">
                    <span
                      className="lean-column__label"
                      style={{ color: col.colorVar }}
                    >
                      {col.label}
                    </span>
                    <span className="lean-column__count">
                      {story[col.key].length} article{story[col.key].length !== 1 ? 's' : ''}
                    </span>
                  </div>

                  <div className="lean-column__articles">
                    {story[col.key].map((article, i) => (
                      <ArticleItem key={article.id} article={article} index={i} />
                    ))}
                  </div>
                </motion.section>
              ))}
            </div>

            <StoryFactSources storyId={story.id} />
          </>
        )}
      </main>
    </motion.div>
  )
}
