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

/**
 * Google Fact Check Tools — professional claim reviews only.
 * Props from parent (StoryFactSources) so WebCite is not bundled here.
 */
export default function FactCheckPanel({ data, loading, error }) {
  return (
    <section className="fact-check-panel">
      <h2 className="fact-check-panel__title">Fact checks</h2>
      <p className="fact-check-panel__intro">
        These entries come from{' '}
        <strong>Google&apos;s Fact Check index</strong> (participating fact-check
        organizations). They are not the same as ordinary news articles.
      </p>

      {loading && (
        <p className="fact-check-panel__state">Loading fact checks…</p>
      )}

      {error && !loading && (
        <p className="fact-check-panel__state fact-check-panel__state--error">
          {error}
        </p>
      )}

      {data && !loading && !error && data.has_results && (
        <h3 className="fact-check-panel__subsection-title">Indexed reviews</h3>
      )}

      {data && !loading && !error && !data.has_results && (
        <div className="fact-check-panel__google-empty">
          <h3 className="fact-check-panel__subsection-title">Indexed reviews</h3>
          <p className="fact-check-panel__message">
            No fact-check article in Google&apos;s index matched this headline yet. That is
            typical for many stories — see <strong>Related coverage</strong> below for news
            links (those are not fact-check verdicts).
          </p>
        </div>
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
