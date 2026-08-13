import React from 'react'

/**
 * LearnGenie mark: an open book with a spark rising from its spine —
 * "genie" (the spark/insight) meeting "learn" (the book), in the same
 * gold/teal/ink palette as the rest of the app. Pure SVG, no external
 * asset, so it scales cleanly for the sidebar, header, and favicon.
 */
export default function Logo({ size = 32, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <rect width="40" height="40" rx="10" fill="#131826" />
      <rect x="0.5" y="0.5" width="39" height="39" rx="9.5" stroke="#262E42" />
      <path
        d="M8 28V13c3.5-1.6 7-1.6 10 0v15c-3-1.6-6.5-1.6-10 0Z"
        fill="none" stroke="#3FA796" strokeWidth="1.6" strokeLinejoin="round"
      />
      <path
        d="M32 28V13c-3.5-1.6-7-1.6-10 0v15c3-1.6 6.5-1.6 10 0Z"
        fill="none" stroke="#3FA796" strokeWidth="1.6" strokeLinejoin="round"
      />
      <path
        d="M20 13v-1.5"
        stroke="#C9A227" strokeWidth="1.6" strokeLinecap="round"
      />
      <path
        d="M20 10.5c0-2.4 1.6-3.6 1.6-5.4 0 1.8 1.8 2.6 1.8 4.6 0 1.7-1.5 2.6-1.9 3.8-.4-1.2-1.5-1.6-1.5-3Z"
        fill="#C9A227"
      />
    </svg>
  )
}