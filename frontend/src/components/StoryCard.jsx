import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import LeanBadge from './LeanBadge.jsx'
import './StoryCard.css'

export default function StoryCard({ story, index = 0 }) {
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

  const heroImage = sorted.find(a => a.image_url)?.image_url || null

  return (
    <motion.article
      className="story-card"
      onClick={() => navigate(`/story/${story.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && navigate(`/story/${story.id}`)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -3, boxShadow: '0 12px 36px rgba(0,0,0,0.12)' }}
      whileTap={{ scale: 0.98 }}
    >
      {heroImage && (
        <div className="story-card__image-wrap">
          <img
            src={heroImage}
            alt=""
            className="story-card__image"
            onError={e => { e.currentTarget.parentElement.style.display = 'none' }}
          />
        </div>
      )}

      <div className="story-card__body">
        <div className="story-card__meta">
          <span className="story-card__time">{timeAgo(story.last_updated_at)}</span>
          <span className="story-card__dot" />
          <span className="story-card__count">{story.article_count} sources</span>
          <div className="story-card__badge-row">
            {story.has_fact_checks && (
              <span className="story-card__fact-checked">✓ FC</span>
            )}
            {story.has_webcite && (
              <span className="story-card__webcite-badge">Sources</span>
            )}
          </div>
        </div>

        <h2 className="story-card__headline">{story.headline}</h2>

        {story.summary && (
          <p className="story-card__summary">{story.summary}</p>
        )}

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
      </div>
    </motion.article>
  )
}
