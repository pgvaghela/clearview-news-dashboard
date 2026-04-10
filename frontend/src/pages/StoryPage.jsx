import { useParams, useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi.js'
import { fetchStory } from '../services/api.js'
import LeanBadge from '../components/LeanBadge.jsx'
import LeanTooltip from '../components/LeanTooltip.jsx'
import FactCheckPanel from '../components/FactCheckPanel.jsx'
import './StoryPage.css'

const LEAN_COLUMNS = [
  { key: 'left',       label: 'Left',       colorVar: 'var(--color-left)' },
  { key: 'lean_left',  label: 'Lean Left',  colorVar: 'var(--color-lean-left)' },
  { key: 'center',     label: 'Center',     colorVar: 'var(--color-center)' },
  { key: 'lean_right', label: 'Lean Right', colorVar: 'var(--color-lean-right)' },
  { key: 'right',      label: 'Right',      colorVar: 'var(--color-right)' },
]

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
    if (diff < 60) return `${diff}m ago`
    if (diff < 1440) return `${Math.floor(diff / 60)}h ago`
    return `${Math.floor(diff / 1440)}d ago`
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
              {LEAN_COLUMNS.map(col => (
                <span
                  key={col.key}
                  className="lean-explainer__chip"
                  style={{ color: col.colorVar }}
                >
                  {col.label}
                </span>
              ))}
            </div>

            <div
              className="lean-columns"
              style={{ '--col-count': filledColumns.length || 3 }}
            >
              {filledColumns.map(col => (
                <section
                  key={col.key}
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

            <FactCheckPanel storyId={story.id} />
          </>
        )}
      </main>
    </div>
  )
}
