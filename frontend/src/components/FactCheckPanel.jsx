import { useApi } from '../hooks/useApi.js'
import { fetchFactChecks } from '../services/api.js'
import './FactCheckPanel.css'

function formatDate(iso) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString()
  } catch {
    return '—'
  }
}

export default function FactCheckPanel({ storyId }) {
  const { data, loading, error } = useApi(
    () => fetchFactChecks(storyId),
    [storyId]
  )

  return (
    <section className="fact-check-panel">
      <h2 className="fact-check-panel__title">Fact checks</h2>

      {loading && (
        <p className="fact-check-panel__state">Loading fact checks…</p>
      )}

      {error && !loading && (
        <p className="fact-check-panel__state fact-check-panel__state--error">
          {error}
        </p>
      )}

      {data && !loading && !error && !data.has_results && (
        <p className="fact-check-panel__message">{data.message}</p>
      )}

      {data && !loading && !error && data.has_results && data.fact_checks?.length > 0 && (
        <ul className="fact-check-panel__list">
          {data.fact_checks.map((fc) => (
            <li key={fc.id} className="fact-check-panel__item">
              <div className="fact-check-panel__item-header">
                <span className="fact-check-panel__publisher">
                  {fc.publisher || 'Unknown publisher'}
                </span>
                <span className="fact-check-panel__date">
                  {formatDate(fc.review_date)}
                </span>
              </div>
              <div className="fact-check-panel__rating">{fc.rating || '—'}</div>
              {fc.review_url && (
                <a
                  href={fc.review_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="fact-check-panel__link"
                >
                  Read review
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
