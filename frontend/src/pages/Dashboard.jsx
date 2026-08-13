import React, { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import MessageContent from '../components/MessageContent'
import FeedbackControls from '../components/FeedbackControls'
import Logo from '../components/Logo'
import ExamPanel from './ExamPanel'

export default function Dashboard() {
  const { courseName } = useParams()
  const navigate = useNavigate()
  const { email, logout } = useAuth()
  const [courses, setCourses] = useState([])
  const [momentum, setMomentum] = useState(null)
  const [view, setView] = useState('exam') // 'exam' | course name

  useEffect(() => {
    api.myCourses().then(setCourses).catch(() => {})
    api.momentum().then(setMomentum).catch(() => {})
  }, [])

  useEffect(() => {
    if (courseName) setView(decodeURIComponent(courseName))
  }, [courseName])

  return (
    <div className="flex h-screen">
      <aside className="flex w-64 shrink-0 flex-col border-r border-hairline bg-surface">
        <div className="border-b border-hairline px-5 py-5">
          <div className="flex items-center gap-2.5">
            <Logo size={28} />
            <p className="font-display text-lg font-medium">LearnGenie</p>
          </div>
          <p className="mt-1 truncate text-xs text-muted">{email}</p>
        </div>

        {momentum && momentum.streak_days > 0 && (
          <div className="mx-3 mt-3 rounded-lg border border-gold/30 bg-gold/10 px-3 py-2">
            <p className="text-sm font-medium text-gold">
              {momentum.streak_days}-day streak 🔥
            </p>
            {momentum.courses[0] && momentum.courses[0].days_since > 0 && (
              <button
                onClick={() => {
                  setView(momentum.courses[0].course_name)
                  navigate(`/dashboard/${encodeURIComponent(momentum.courses[0].course_name)}`)
                }}
                className="mt-0.5 block text-left text-xs text-muted hover:text-parchment"
              >
                Pick up {momentum.courses[0].course_name} — last studied {momentum.courses[0].days_since}d ago
              </button>
            )}
          </div>
        )}

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          <p className="citation-tab px-2 pb-2 text-[10px] uppercase tracking-[0.15em] text-muted">
            Your courses
          </p>
          {courses.map((c) => (
            <button
              key={c}
              onClick={() => {
                setView(c)
                navigate(`/dashboard/${encodeURIComponent(c)}`)
              }}
              className={`block w-full rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                view === c ? 'bg-gold/15 text-gold' : 'text-parchment/85 hover:bg-raised'
              }`}
            >
              {c}
            </button>
          ))}

          <div className="pt-4">
            <button
              onClick={() => {
                setView('exam')
                navigate('/dashboard')
              }}
              className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                view === 'exam' ? 'bg-teal/15 text-teal' : 'text-parchment/85 hover:bg-raised'
              }`}
            >
              Examination panel
              <span className="citation-tab rounded-full bg-hairline px-1.5 py-0.5 text-[9px] text-muted">soon</span>
            </button>
          </div>

          <Link
            to="/courses"
            className="mt-4 block rounded-lg px-3 py-2.5 text-sm text-muted hover:bg-raised hover:text-parchment"
          >
            + Manage courses
          </Link>
        </nav>

        <div className="border-t border-hairline p-3">
          <button
            onClick={logout}
            className="w-full rounded-lg px-3 py-2 text-left text-sm text-muted hover:bg-raised hover:text-rust"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {view === 'exam' ? (
            <motion.div key="exam" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
              <ExamPanel courses={courses} />
            </motion.div>
          ) : (
            <motion.div key={view} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
              <CourseChat course={view} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}

const THINKING_PHRASES = [
  'Digging through your material…',
  'Checking your notes on this…',
  'Working through it…',
  'Pulling this from your course PDFs…',
]

function CourseChat({ course }) {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const [loaded, setLoaded] = useState(false)
  const [thinkingPhrase, setThinkingPhrase] = useState(THINKING_PHRASES[0])
  const bottomRef = useRef(null)

  useEffect(() => {
    setLoaded(false)
    setMessages([])
    api
      .getMessages(course)
      .then(setMessages)
      .catch((e) => setError(e.message))
      .finally(() => setLoaded(true))
  }, [course])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e) {
    e.preventDefault()
    const content = draft.trim()
    if (!content || sending) return
    setDraft('')
    setError(null)
    setMessages((m) => [...m, { role: 'user', content, created_at: new Date().toISOString() }])
    setThinkingPhrase(THINKING_PHRASES[Math.floor(Math.random() * THINKING_PHRASES.length)])
    setSending(true)
    try {
      const reply = await api.sendMessage(course, content)
      setMessages((m) => [...m, reply])
    } catch (e2) {
      setError(e2.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-hairline px-8 py-5">
        <p className="citation-tab text-xs uppercase tracking-[0.15em] text-teal">course chat</p>
        <h2 className="mt-1 font-display text-2xl font-medium">{course}</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {loaded && messages.length === 0 && (
          <div className="mx-auto max-w-3xl">
            <div className="rounded-2xl border border-hairline bg-raised px-5 py-4">
              <p className="font-display text-lg">Ready when you are.</p>
              <p className="mt-1 text-sm text-muted">
                Ask me anything from your {course} material — a concept, a comparison, "explain X like I'm studying
                for the exam." Say "diagram" or "flowchart" if a visual would help it click.
              </p>
            </div>
          </div>
        )}
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.map((m, i) => (
            <div key={m.id ?? i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                  m.role === 'user'
                    ? 'bg-gold/15 text-parchment'
                    : 'border border-hairline bg-raised text-parchment'
                }`}
              >
                <MessageContent text={m.content} />
              </div>
              {m.role === 'assistant' && m.id && (
                <FeedbackControls
                  messageId={m.id}
                  onCorrected={(corrected) => setMessages((prev) => [...prev, corrected])}
                />
              )}
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl border border-hairline bg-raised px-4 py-3 text-sm text-muted">
                <span className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal" />
                </span>
                {thinkingPhrase}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {error && <p className="px-8 pb-2 text-sm text-rust">{error}</p>}

      <form onSubmit={handleSend} className="border-t border-hairline p-4">
        <div className="mx-auto flex max-w-3xl items-end gap-3">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend(e)
              }
            }}
            rows={1}
            placeholder={`Ask about ${course}…`}
            className="flex-1 resize-none rounded-lg border border-hairline bg-surface px-4 py-3 text-sm outline-none focus:border-gold"
          />
          <button
            type="submit"
            disabled={sending || !draft.trim()}
            className="rounded-lg bg-gold px-5 py-3 text-sm font-semibold text-ink transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  )
}