import { useParams, useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi.js'
import { fetchStory } from '../services/api.js'
import LeanBadge from '../components/LeanBadge.jsx'
import LeanTooltip from '../components/LeanTooltip.jsx'
import './StoryPage.css'

// ── Mock data — used until API wiring is complete (Sprint 1) ──────────────
const MOCK_STORY = {
  id: 1,
  headline: 'Senate passes major infrastructure bill after weeks of debate',
  first_seen_at: new Date(Date.now() - 180 * 60000).toISOString(),
  last_updated_at: new Date(Date.now() - 20 * 60000).toISOString(),
  article_count: 6,
  lean_categories_present: 'left,center,right',
  left: [
    {
      id: 1,
      title: 'Historic infrastructure bill delivers for working families',
      url: 'https://npr.org/example',
      description: 'The sweeping package includes funding for broadband, clean energy, and public transit.',
      published_at: new Date(Date.now() - 90 * 60000).toISOString(),
      outlet_name: 'NPR',
      lean_display: 'Left',
      why_label: 'NPR is rated Left by AllSides based on blind reader surveys conducted annually.',
      rating_provider: 'AllSides',
      rating_method: 'Blind surveys',
      confidence: 'Community consensus',
    },
    {
      id: 2,
      title: 'Infrastructure vote marks major progressive victory',
      url: 'https://huffpost.com/example',
      description: 'Advocates celebrated the passage as a once-in-a-generation investment.',
      published_at: new Date(Date.now() - 120 * 60000).toISOString(),
      outlet_name: 'HuffPost',
      lean_display: 'Left',
      why_label: 'HuffPost is rated Left by AllSides based on blind reader surveys.',
      rating_provider: 'AllSides',
      rating_method: 'Blind surveys',
      confidence: 'Community consensus',
    },
  ],
  lean_left: [],
  center: [
    {
      id: 3,
      title: 'Senate approves $1.2 trillion infrastructure package',
      url: 'https://reuters.com/example',
      description: 'The bill passed 69-30 with bipartisan support, heading next to the House.',
      published_at: new Date(Date.now() - 60 * 60000).toISOString(),
      outlet_name: 'Reuters',
      lean_display: 'Center',
      why_label: 'Reuters is rated Center by AllSides based on multi-partisan editorial review and reader surveys.',
      rating_provider: 'AllSides',
      rating_method: 'Multi-partisan panel review + blind surveys',
      confidence: 'Community consensus',
    },
    {
      id: 4,
      title: 'Infrastructure bill passes Senate in bipartisan vote',
      url: 'https://apnews.com/example',
      description: 'The Associated Press reported 19 Republicans joined all 50 Democrats.',
      published_at: new Date(Date.now() - 75 * 60000).toISOString(),
      outlet_name: 'Associated Press',
      lean_display: 'Center',
      why_label: 'AP is rated Center by AllSides.',
      rating_provider: 'AllSides',
      rating_method: 'Multi-partisan panel review + blind surveys',
      confidence: 'Community consensus',
    },
  ],
  lean_right: [],
  right: [
    {
      id: 5,
      title: 'Infrastructure bill a trojan horse for Green New Deal spending',
      url: 'https://foxnews.com/example',
      description: 'Critics say the $1.2 trillion price tag masks climate provisions buried in the text.',
      published_at: new Date(Date.now() - 45 * 60000).toISOString(),
      outlet_name: 'Fox News',
      lean_display: 'Right',
      why_label: 'Fox News is rated Right by AllSides based on blind reader surveys.',
      rating_provider: 'AllSides',
      rating_method: 'Blind surveys',
      confidence: 'Community consensus',
    },
  ],
}

const USE_MOCK = true  // flip to false once API wiring is complete

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
    () => USE_MOCK ? Promise.resolve(MOCK_STORY) : fetchStory(id),
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

            {/* Fact-check panel — Sprint 2 placeholder */}
            <section className="factcheck-panel factcheck-panel--placeholder">
              <h2 className="factcheck-panel__title">Fact Checks</h2>
              <p className="factcheck-panel__coming-soon">
                Fact-check panel coming in Sprint 2 (04/03 – 04/17).
              </p>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
