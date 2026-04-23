import { useState } from 'react'
import './LeanTooltip.css'

/**
 * Renders a "Why this label?" button that toggles an explanation panel.
 *
 * Props:
 *   whyLabel        {string}  — plain-language explanation
 *   ratingProvider  {string}  — e.g. "AllSides"
 *   ratingMethod    {string}  — e.g. "Blind surveys"
 *   confidence      {string}  — e.g. "Community consensus"
 */
export default function LeanTooltip({ whyLabel, ratingProvider, ratingMethod, confidence }) {
  const [open, setOpen] = useState(false)

  if (!whyLabel) return null

  return (
    <span className="lean-tooltip-wrapper">
      <button
        className="why-label-btn"
        onClick={(e) => {
          e.stopPropagation()
          setOpen((o) => !o)
        }}
        aria-expanded={open}
      >
        Why this label?
      </button>

      {open && (
        <div
          className="lean-tooltip-panel"
          role="tooltip"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            type="button"
            className="tooltip-close"
            onClick={(e) => {
              e.stopPropagation()
              setOpen(false)
            }}
            aria-label="Close"
          >
            ✕
          </button>

          {ratingProvider && (
            <p className="tooltip-row">
              <span className="tooltip-label">Provider:</span> {ratingProvider}
            </p>
          )}
          {ratingMethod && (
            <p className="tooltip-row">
              <span className="tooltip-label">Method:</span> {ratingMethod}
            </p>
          )}
          {confidence && (
            <p className="tooltip-row">
              <span className="tooltip-label">Confidence:</span> {confidence}
            </p>
          )}
          <p className="tooltip-explanation">{whyLabel}</p>
        </div>
      )}
    </span>
  )
}
