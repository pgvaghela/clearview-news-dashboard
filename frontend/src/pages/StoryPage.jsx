import { useParams, useNavigate } from 'react-router-dom'
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

function scrollToLeanColumn(key) {
  document.getElementById(`story-lean-${key}`)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

function ArticleItem({ article }) {
  return (
    <div className="article-item">
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
    </div>
  )
}

export default function StoryPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: story, loading, error } = useApi(
    () => fetchStory(id),
    [id]
  )

  const filledColumns = LEAN_COLUMNS.filter(
    col => story && (story[col.key] || []).length > 0
  )

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
    <div className="story-page">
      <header className="story-page__header">
        <div className="story-page__header-inner">
          <button className="back-btn" onClick={() => navigate('/')}>
            ← ClearView
          </button>

          {story && (
            <>
              <h1 className="story-page__headline">{story.headline}</h1>
              <div className="story-page__meta">
                <span>{story.article_count} sources</span>
                <span>·</span>
                <span>Updated {timeAgo(story.last_updated_at)}</span>
              </div>
            </>
          )}
        </div>
      </header>

      <main className="story-page__main">
        {loading && <div className="story-page__state">Loading story…</div>}

        {error && (
          <div className="story-page__state story-page__state--error">
            {error}
          </div>
        )}

        {story && !loading && (
          <>
            <div className="lean-explainer">
              <span className="lean-explainer__text">
                Coverage grouped by political lean —
              </span>
              {LEAN_COLUMNS.map(col => {
                const count = (story[col.key] || []).length
                if (count > 0) {
                  return (
                    <button
                      key={col.key}
                      type="button"
                      className="lean-explainer__chip lean-explainer__chip--link"
                      style={{ color: col.colorVar }}
                      onClick={() => scrollToLeanColumn(col.key)}
                    >
                      {col.label}
                    </button>
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
            </div>

            <div
              className="lean-columns"
              style={{ '--col-count': filledColumns.length || 3 }}
            >
              {filledColumns.map(col => (
                <section
                  key={col.key}
                  id={`story-lean-${col.key}`}
                  className="lean-column"
                  style={{ '--col-color': col.colorVar }}
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
                    {story[col.key].map(article => (
                      <ArticleItem key={article.id} article={article} />
                    ))}
                  </div>
                </section>
              ))}
            </div>

            <StoryFactSources storyId={story.id} />
          </>
        )}
      </main>
    </div>
  )
}
