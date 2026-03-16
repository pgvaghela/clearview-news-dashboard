import { useNavigate } from 'react-router-dom'
import LeanBadge from './LeanBadge.jsx'
import './StoryCard.css'

/**
 * Dashboard story card.
 * Shows headline, timestamp, source badges, and navigates to StoryPage on click.
 */
export default function StoryCard({ story }) {
  const navigate = useNavigate()

  const timeAgo = (dateStr) => {
    const diff = Math.floor((Date.now() - new Date(dateStr)) / 60000)
    if (diff < 1) return 'just now'
    if (diff < 60) return `${diff}m ago`
    if (diff < 1440) return `${Math.floor(diff / 60)}h ago`
    return `${Math.floor(diff / 1440)}d ago`
  }

  const leanOrder = ['Left', 'Lean Left', 'Center', 'Lean Right', 'Right']
  const sorted = [...(story.preview_articles || [])].sort(
    (a, b) => leanOrder.indexOf(a.lean_display) - leanOrder.indexOf(b.lean_display)
  )

  return (
    <article
      className="story-card"
      onClick={() => navigate(`/story/${story.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && navigate(`/story/${story.id}`)}
    >
      <div className="story-card__meta">
        <span className="story-card__time">{timeAgo(story.last_updated_at)}</span>
        <span className="story-card__count">{story.article_count} sources</span>
      </div>

      <h2 className="story-card__headline">{story.headline}</h2>

      <div className="story-card__badges">
        {sorted.map(article => (
          <LeanBadge key={article.id} lean={article.lean_display} />
        ))}
      </div>

      <div className="story-card__sources">
        {sorted.map(article => (
          <span key={article.id} className="story-card__source">
            {article.outlet_name}
          </span>
        ))}
      </div>
    </article>
  )
}
