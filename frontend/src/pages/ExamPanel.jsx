import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../api/client'

export default function ExamPanel({ courses }) {
  const [course, setCourse] = useState(courses[0] || null)
  const [stage, setStage] = useState('intro') // intro | loading | quiz | done
  const [questions, setQuestions] = useState([])
  const [index, setIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [grading, setGrading] = useState(false)
  const [results, setResults] = useState([]) // {question, topic, answer, is_correct, feedback}
  const [error, setError] = useState(null)
  const [plan, setPlan] = useState(null)

  useEffect(() => {
    if (!course) return
    setStage('intro')
    setResults([])
    setIndex(0)
    api.studyPlan(course).then(setPlan).catch(() => setPlan(null))
  }, [course])

  if (!course) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-8 text-center">
        <span className="citation-tab rounded-full border border-hairline px-3 py-1 text-xs text-muted">
          examination panel
        </span>
        <p className="mt-4 max-w-sm text-sm text-muted">
          Select at least one course from the dashboard first — quizzes are generated from a specific course's
          material.
        </p>
      </div>
    )
  }

  async function startQuiz() {
    setStage('loading')
    setError(null)
    try {
      const qs = await api.generateQuiz(course, 5)
      setQuestions(qs)
      setIndex(0)
      setResults([])
      setStage('quiz')
    } catch (e) {
      setError(e.message)
      setStage('intro')
    }
  }

  async function submitAnswer() {
    if (!answer.trim() || grading) return
    setGrading(true)
    setError(null)
    const current = questions[index]
    try {
      const graded = await api.gradeAnswer(course, String(index), current.question, current.topic, answer)
      setResults((r) => [...r, { ...current, answer, ...graded }])
      setAnswer('')
      if (index + 1 < questions.length) {
        setIndex(index + 1)
      } else {
        setStage('done')
        api.studyPlan(course).then(setPlan).catch(() => {})
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setGrading(false)
    }
  }

  if (stage === 'intro') {
    return (
      <div className="flex h-full flex-col items-center justify-center px-8 text-center">
        <span className="citation-tab rounded-full border border-hairline px-3 py-1 text-xs text-muted">
          examination panel
        </span>

        {courses.length > 1 && (
          <select
            value={course}
            onChange={(e) => setCourse(e.target.value)}
            className="mt-4 rounded-lg border border-hairline bg-surface px-3 py-1.5 text-sm outline-none focus:border-gold"
          >
            {courses.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        )}

        <h2 className="mt-4 font-display text-2xl font-medium">Quiz yourself on {course}</h2>
        <p className="mt-2 max-w-md text-sm text-muted">
          Five questions generated from your course material, graded against the actual source — not a canned
          answer key.
        </p>

        {plan && (
          <div className="mt-6 max-w-md rounded-xl border border-hairline bg-raised px-4 py-3 text-sm text-parchment/85">
            <span className="citation-tab text-teal">plan · </span>
            {plan.suggestion}
          </div>
        )}

        {error && <p className="mt-4 text-sm text-rust">{error}</p>}

        <button
          onClick={startQuiz}
          className="mt-6 rounded-lg bg-gold px-6 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
        >
          Start quiz
        </button>
      </div>
    )
  }

  if (stage === 'loading') {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-muted">
          <span className="flex gap-1">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold" />
          </span>
          Writing questions from your material…
        </div>
      </div>
    )
  }

  if (stage === 'quiz') {
    const current = questions[index]
    return (
      <div className="mx-auto flex h-full max-w-2xl flex-col justify-center px-8">
        <p className="citation-tab mb-2 text-xs text-muted">
          question {index + 1} of {questions.length} · {current.topic}
        </p>
        <motion.div key={index} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <p className="font-display text-xl">{current.question}</p>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={4}
            placeholder="Your answer…"
            className="w-full resize-none rounded-lg border border-hairline bg-surface px-4 py-3 text-sm outline-none focus:border-gold"
          />
          {error && <p className="text-sm text-rust">{error}</p>}
          <button
            onClick={submitAnswer}
            disabled={grading || !answer.trim()}
            className="rounded-lg bg-gold px-6 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            {grading ? 'Grading…' : index + 1 === questions.length ? 'Submit & finish' : 'Submit answer'}
          </button>
        </motion.div>
      </div>
    )
  }

  // stage === 'done'
  const correctCount = results.filter((r) => r.is_correct).length
  return (
    <div className="mx-auto h-full max-w-2xl overflow-y-auto px-8 py-10">
      <p className="citation-tab text-xs uppercase tracking-[0.15em] text-teal">results</p>
      <h2 className="mt-1 font-display text-2xl font-medium">
        {correctCount} / {results.length} correct
      </h2>

      {plan && (
        <div className="mt-4 rounded-xl border border-hairline bg-raised px-4 py-3 text-sm text-parchment/85">
          <span className="citation-tab text-teal">plan · </span>
          {plan.suggestion}
        </div>
      )}

      <div className="mt-6 space-y-4">
        <AnimatePresence>
          {results.map((r, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`rounded-xl border px-4 py-3 ${r.is_correct ? 'border-teal/40 bg-teal/5' : 'border-rust/40 bg-rust/5'}`}
            >
              <div className="flex items-center justify-between">
                <span className="citation-tab text-xs text-muted">{r.topic}</span>
                <span className={`text-xs font-semibold ${r.is_correct ? 'text-teal' : 'text-rust'}`}>
                  {r.is_correct ? 'Correct' : 'Needs work'}
                </span>
              </div>
              <p className="mt-1 text-sm font-medium">{r.question}</p>
              <p className="mt-1 text-xs text-muted">Your answer: {r.answer}</p>
              <p className="mt-2 text-sm leading-relaxed">{r.feedback}</p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <button
        onClick={startQuiz}
        className="mt-8 rounded-lg border border-hairline px-5 py-2.5 text-sm font-medium hover:bg-raised"
      >
        Take another quiz
      </button>
    </div>
  )
}
