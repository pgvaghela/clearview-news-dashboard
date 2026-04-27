/**
 * Framer Motion stub for unit tests.
 * All animated components render immediately with no delays so tests stay synchronous.
 */
import React from 'react'

// Proxy creates motion.div, motion.article, motion.button, etc. on demand —
// each one strips animation props and renders the plain HTML element.
const motion = new Proxy({}, {
  get(_, tag) {
    const Component = React.forwardRef(function MotionStub(
      {
        children,
        initial, animate, exit, transition, variants,
        whileHover, whileTap, whileFocus,
        onAnimationStart, onAnimationComplete,
        ...rest
      },
      ref
    ) {
      return React.createElement(tag, { ...rest, ref }, children)
    })
    Component.displayName = `motion.${tag}`
    return Component
  },
})

// AnimatePresence: just renders children — no exit-animation delay.
function AnimatePresence({ children }) {
  return <>{children}</>
}

export { motion, AnimatePresence }
