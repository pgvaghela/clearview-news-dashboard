import './WebcitePanel.css'

/**
 * WebCite source search — separate from professional fact-checks.
 * Does not produce a fact-check verdict; only surfaces related URLs/snippets.
 */
export default function WebcitePanel({ webcite, loading, error }) {
  if (error || loading) return null

  const wc = webcite
  if (!wc || !wc.available) return null

  const hasSources =
    wc.status === 'ok' && wc.citations && wc.citations.length > 0

  return (
    <section className="webcite-panel" aria-label="Related coverage from WebCite">
      <h2 className="webcite-panel__title">Related coverage</h2>
      <p className="webcite-panel__disclaimer">
        WebCite searches the web for pages related to this headline. This is{' '}
        <strong>not</strong> a fact-check and <strong>not</strong> a true/false verdict — only
        starting points for your own reading.
      </p>

      {hasSources && (
        <>
          <p className="webcite-panel__vendor">Powered by WebCite (source search)</p>
          <ul className="webcite-panel__list">
            {wc.citations.map((c, i) => (
              <li key={c.url || i} className="webcite-panel__item">
                {c.url ? (
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="webcite-panel__link"
                  >
                    {c.title || c.url}
                  </a>
                ) : (
                  <span className="webcite-panel__title-only">{c.title || 'Source'}</span>
                )}
                <div className="webcite-panel__meta">
                  {c.source_type && <span>{c.source_type}</span>}
                  {c.credibility_score != null && (
                    <span>Relevance score {c.credibility_score}</span>
                  )}
                </div>
                {c.snippet && <p className="webcite-panel__snippet">{c.snippet}</p>}
              </li>
            ))}
          </ul>
        </>
      )}

      {wc.status === 'no_data' && (
        <p className="webcite-panel__state">{wc.message}</p>
      )}

      {wc.status === 'error' && (
        <p className="webcite-panel__state webcite-panel__state--error">{wc.message}</p>
      )}
    </section>
  )
}
