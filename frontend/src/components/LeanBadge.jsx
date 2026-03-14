import './LeanBadge.css'

const LEAN_COLORS = {
  'Left':       'var(--color-left)',
  'Lean Left':  'var(--color-lean-left)',
  'Center':     'var(--color-center)',
  'Lean Right': 'var(--color-lean-right)',
  'Right':      'var(--color-right)',
}

/**
 * Displays a coloured pill showing the political lean of a source.
 * e.g. <LeanBadge lean="Left" />
 */
export default function LeanBadge({ lean }) {
  if (!lean || lean === 'Unknown') return null
  const color = LEAN_COLORS[lean] || 'var(--color-text-muted)'
  return (
    <span className="lean-badge" style={{ borderColor: color, color }}>
      {lean}
    </span>
  )
}
