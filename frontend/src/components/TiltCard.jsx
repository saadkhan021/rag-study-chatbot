import React, { useRef, useState } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'

/**
 * A card that tilts toward the cursor in 3D, like an index card being
 * lifted off a desk. Respects prefers-reduced-motion by disabling the
 * spring-driven tilt (CSS media query in index.css handles the rest).
 */
export default function TiltCard({ children, className = '', onClick, glow = 'gold' }) {
  const ref = useRef(null)
  const [hovering, setHovering] = useState(false)

  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [10, -10]), { stiffness: 220, damping: 20 })
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-10, 10]), { stiffness: 220, damping: 20 })
  const glowX = useTransform(x, [-0.5, 0.5], ['20%', '80%'])
  const glowY = useTransform(y, [-0.5, 0.5], ['20%', '80%'])

  function handleMouseMove(e) {
    const rect = ref.current.getBoundingClientRect()
    x.set((e.clientX - rect.left) / rect.width - 0.5)
    y.set((e.clientY - rect.top) / rect.height - 0.5)
  }

  function handleLeave() {
    x.set(0)
    y.set(0)
    setHovering(false)
  }

  const glowColor = glow === 'teal' ? 'rgba(63,167,150,0.25)' : 'rgba(201,162,39,0.25)'

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={handleLeave}
      onClick={onClick}
      style={{ rotateX, rotateY, transformPerspective: 900 }}
      whileHover={{ scale: 1.02, y: -4 }}
      className={`relative rounded-xl border border-hairline bg-raised shadow-card transition-shadow ${className}`}
    >
      <motion.div
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-xl opacity-0"
        animate={{ opacity: hovering ? 1 : 0 }}
        style={{
          background: `radial-gradient(circle at ${glowX} ${glowY}, ${glowColor}, transparent 60%)`,
        }}
      />
      <div className="relative">{children}</div>
    </motion.div>
  )
}
