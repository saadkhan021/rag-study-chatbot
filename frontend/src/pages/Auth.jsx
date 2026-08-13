import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import TiltCard from '../components/TiltCard'
import Logo from '../components/Logo'

export default function Auth() {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const { login, signup } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (mode === 'login') await login(email, password)
      else await signup(email, password)
      navigate('/courses')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mb-3 flex justify-center">
            <Logo size={48} />
          </div>
          <p className="citation-tab text-xs uppercase tracking-[0.2em] text-teal">study assistant</p>
          <h1 className="mt-2 font-display text-4xl font-medium tracking-tight">LearnGenie</h1>
          <p className="mt-2 text-sm text-muted">Answers grounded in your own course material — nothing invented.</p>
        </div>

        <TiltCard className="p-8" glow="teal">
          <div className="mb-6 flex rounded-lg bg-surface p-1">
            {['login', 'signup'].map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 rounded-md py-2 text-sm font-medium transition-colors ${
                  mode === m ? 'bg-gold/20 text-gold' : 'text-muted hover:text-parchment'
                }`}
              >
                {m === 'login' ? 'Log in' : 'Sign up'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-xs text-muted">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-hairline bg-surface px-3 py-2.5 text-sm outline-none focus:border-gold"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted">Password</label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-hairline bg-surface px-3 py-2.5 text-sm outline-none focus:border-gold"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-lg border border-rust/40 bg-rust/10 px-3 py-2 text-sm text-rust"
              >
                {error}
              </motion.p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-gold py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {busy ? 'Working…' : mode === 'login' ? 'Log in' : 'Create account'}
            </button>
          </form>
        </TiltCard>
      </div>
    </div>
  )
}