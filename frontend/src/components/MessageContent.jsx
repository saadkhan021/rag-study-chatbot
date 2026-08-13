import React from 'react'
import MermaidBlock from './MermaidBlock'

/**
 * Splits assistant text on ```mermaid fenced blocks (rendered as actual
 * diagrams) and renders everything else through a small markdown-lite
 * pass: **bold**, bullet lists (using * or - ), and paragraphs. Also
 * highlights [source.pdf, page N]-style citation tags as gold tabs.
 *
 * Not a full CommonMark implementation on purpose — it only needs to
 * cover the formatting the system prompt in rag.py actually produces.
 * If you change the prompt's output style, extend this to match.
 */
export default function MessageContent({ text }) {
  // Mermaid fences become real diagrams; any other fenced code block
  // (in case the model doesn't follow the mermaid instruction) still
  // renders as a clean code block instead of showing raw backticks.
  const parts = text.split(/```(mermaid)?\n?([\s\S]*?)```/g)

  return (
    <div className="space-y-2">
      {parts.map((part, i) => {
        const mod = i % 3
        if (mod === 1) return null // capture group placeholder, language tag handled below
        if (mod === 2) {
          const language = parts[i - 1]
          return language === 'mermaid' ? (
            <MermaidBlock key={i} code={part.trim()} />
          ) : (
            <pre key={i} className="overflow-x-auto rounded-lg border border-hairline bg-surface p-3 text-xs text-parchment/90">
              <code>{part.trim()}</code>
            </pre>
          )
        }
        return <MarkdownLite key={i} text={part} />
      })}
    </div>
  )
}

function MarkdownLite({ text }) {
  if (!text.trim()) return null

  // Group consecutive bullet lines into <ul> blocks; everything else is a paragraph.
  const lines = text.split('\n')
  const blocks = []
  let currentList = null

  for (const rawLine of lines) {
    const line = rawLine.trim()
    const bulletMatch = line.match(/^[*-]\s+(.*)/)
    if (bulletMatch) {
      if (!currentList) {
        currentList = []
        blocks.push({ type: 'list', items: currentList })
      }
      currentList.push(bulletMatch[1])
    } else {
      currentList = null
      if (line) blocks.push({ type: 'p', text: line })
    }
  }

  return (
    <>
      {blocks.map((block, i) =>
        block.type === 'list' ? (
          <ul key={i} className="ml-4 list-disc space-y-1">
            {block.items.map((item, j) => (
              <li key={j} className="leading-relaxed">
                <Inline text={item} />
              </li>
            ))}
          </ul>
        ) : (
          <p key={i} className="leading-relaxed">
            <Inline text={block.text} />
          </p>
        )
      )}
    </>
  )
}

/** Renders **bold** spans and [citation, page N] tags within one line/item. */
function Inline({ text }) {
  const segments = text.split(/(\*\*[^*]+\*\*|\[[^\[\]]+?\])/g)
  return segments.map((seg, i) => {
    if (/^\*\*[^*]+\*\*$/.test(seg)) {
      return <strong key={i} className="font-semibold text-gold">{seg.slice(2, -2)}</strong>
    }
    if (/^\[.+\]$/.test(seg) && /pdf|page/i.test(seg)) {
      return (
        <span key={i} className="citation-tab mx-0.5 inline-block rounded bg-gold/15 px-1.5 py-0.5 text-xs text-gold align-middle">
          {seg.replace(/[[\]]/g, '')}
        </span>
      )
    }
    return <React.Fragment key={i}>{seg}</React.Fragment>
  })
}
