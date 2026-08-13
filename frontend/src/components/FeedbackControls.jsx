import React, { useState } from 'react'
import { api } from '../api/client'

/**
 * Thumbs up/down under an assistant message. Thumbs-down opens an inline
 * "what's wrong?" note and, on submit, calls /messages/{id}/regenerate —
 * the corrected reply comes back through onCorrected() so the parent can
 * append it to the transcript as a new message.
 */
export default function FeedbackControls({ messageId, onCorrected }) {
  const [rated, setRated] = useState(null) // null | 'up' | 'down'
  const [showNote, setShowNote] = useState(false)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  async function thumbsUp() {
    if (rated) return
    setRated('up')
    try {
      await api.rateMessage(messageId, 'up')
    } catch {
      // Non-critical — don't block the UI on a feedback-logging failure.
    }
  }

  function thumbsDown() {
    if (rated) return
    setShowNote(true)
  }

  async function submitCorrection() {
    setBusy(true)
    try {
      setRated('down')
      const corrected = await api.regenerateMessage(messageId, note.trim() || null)
      onCorrected(corrected)
      setDone(true)
      setShowNote(false)
    } catch {
      // Leave the note box open so they can retry.
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return <p className="mt-1 text-xs text-teal">Thanks — sent you a corrected answer above.</p>
  }

  return (
    <div className="mt-1.5">
      <div className="flex items-center gap-2">
        <button
          onClick={thumbsUp}
          disabled={!!rated}
          className={`rounded px-1.5 py-0.5 text-xs transition-colors ${
            rated === 'up' ? 'text-teal' : 'text-muted hover:text-parchment disabled:opacity-40'
          }`}
          title="Good answer"
        >
          👍
        </button>
        <button
          onClick={thumbsDown}
          disabled={!!rated}
          className={`rounded px-1.5 py-0.5 text-xs transition-colors ${
            rated === 'down' ? 'text-rust' : 'text-muted hover:text-parchment disabled:opacity-40'
          }`}
          title="Something's wrong"
        >
          👎
        </button>
      </div>

      {showNote && (
        <div className="mt-2 max-w-sm rounded-lg border border-hairline bg-surface p-2">
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            placeholder="What's wrong with this answer? (optional, but helps)"
            className="w-full resize-none rounded bg-transparent text-xs outline-none placeholder:text-muted"
            autoFocus
          />
          <div className="mt-1 flex justify-end gap-2">
            <button
              onClick={() => setShowNote(false)}
              className="rounded px-2 py-1 text-xs text-muted hover:text-parchment"
            >
              Cancel
            </button>
            <button
              onClick={submitCorrection}
              disabled={busy}
              className="rounded bg-gold px-2.5 py-1 text-xs font-semibold text-ink hover:opacity-90 disabled:opacity-50"
            >
              {busy ? 'Fixing…' : 'Get corrected answer'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
