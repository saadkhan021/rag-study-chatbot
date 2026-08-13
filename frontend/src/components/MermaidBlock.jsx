import React, { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'

let initialized = false
function ensureInit() {
  if (initialized) return
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    themeVariables: {
      background: '#131826',
      primaryColor: '#1B2233',
      primaryTextColor: '#ECE8DC',
      primaryBorderColor: '#C9A227',
      lineColor: '#3FA796',
      secondaryColor: '#1B2233',
      tertiaryColor: '#131826',
      fontFamily: 'Inter, sans-serif',
    },
  })
  initialized = true
}

/** Renders a single mermaid diagram from raw mermaid syntax. */
export default function MermaidBlock({ code }) {
  const containerRef = useRef(null)
  const [error, setError] = useState(null)
  const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2)}`)

  useEffect(() => {
    ensureInit()
    let cancelled = false
    mermaid
      .render(idRef.current, code)
      .then(({ svg }) => {
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg
          setError(null)
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message || 'Could not render diagram')
      })
    return () => {
      cancelled = true
    }
  }, [code])

  if (error) {
    return (
      <div className="rounded-lg border border-rust/40 bg-rust/10 p-3 text-sm text-rust">
        Diagram couldn't render — showing raw source instead.
        <pre className="mt-2 overflow-x-auto text-xs text-muted">{code}</pre>
      </div>
    )
  }

  return (
    <div className="my-2 overflow-x-auto rounded-lg border border-hairline bg-surface p-4">
      <div ref={containerRef} />
    </div>
  )
}
