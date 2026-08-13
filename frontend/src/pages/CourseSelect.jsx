import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import TiltCard from '../components/TiltCard'

const SUBJECT_CODE = {
  'AI': 'AI',
  'Agentic AI': 'AGT',
  'Generative AI': 'GEN',
  'Computer Science': 'CS',
  'Software Engineering': 'SWE',
  'BBA': 'BBA',
  'Finance': 'FIN',
}

export default function CourseSelect() {
  const [available, setAvailable] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([api.listAvailableCourses(), api.myCourses()])
      .then(([avail, mine]) => {
        setAvailable(avail.courses)
        setSelected(new Set(mine))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function toggle(course) {
    const next = new Set(selected)
    try {
      if (next.has(course)) {
        await api.removeCourse(course)
        next.delete(course)
      } else {
        await api.addCourse(course)
        next.add(course)
      }
      setSelected(next)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <div className="mb-10">
        <p className="citation-tab text-xs uppercase tracking-[0.2em] text-teal">01 · select your subjects</p>
        <h1 className="mt-2 font-display text-3xl font-medium tracking-tight">
          Pick what you're studying
        </h1>
        <p className="mt-2 text-sm text-muted">
          Each subject gets its own persistent conversation, grounded only in that subject's material. Add or remove any time.
        </p>
      </div>

      {error && <p className="mb-4 text-sm text-rust">{error}</p>}

      {loading ? (
        <p className="text-sm text-muted">Loading courses…</p>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {available.map((course, i) => {
            const active = selected.has(course)
            return (
              <motion.div
                key={course}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
              >
                <TiltCard
                  onClick={() => toggle(course)}
                  glow={active ? 'gold' : 'teal'}
                  className={`cursor-pointer p-6 ${active ? 'border-gold/60' : ''}`}
                >
                  <div className="flex items-start justify-between">
                    <span className="citation-tab rounded bg-surface px-2 py-1 text-xs text-muted">
                      {SUBJECT_CODE[course] || course.slice(0, 3).toUpperCase()}
                    </span>
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${active ? 'bg-gold' : 'bg-hairline'}`}
                      aria-hidden
                    />
                  </div>
                  <h3 className="mt-4 font-display text-xl font-medium">{course}</h3>
                  <p className="mt-1 text-xs text-muted">
                    {active ? 'Selected — tap to remove' : 'Tap to add to your dashboard'}
                  </p>
                </TiltCard>
              </motion.div>
            )
          })}
        </div>
      )}

      <div className="mt-10 flex justify-end">
        <button
          onClick={() => navigate('/dashboard')}
          disabled={selected.size === 0}
          className="rounded-lg bg-gold px-6 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          Go to dashboard →
        </button>
      </div>
    </div>
  )
}
