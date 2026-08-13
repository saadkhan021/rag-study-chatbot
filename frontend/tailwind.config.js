/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0B0F19',
        surface: '#131826',
        raised: '#1B2233',
        hairline: '#262E42',
        parchment: '#ECE8DC',
        muted: '#8890A6',
        gold: '#C9A227',
        teal: '#3FA796',
        rust: '#C15B4A',
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      boxShadow: {
        card: '0 20px 40px -12px rgba(0,0,0,0.55)',
        tab: '0 2px 6px rgba(201,162,39,0.35)',
      },
    },
  },
  plugins: [],
}
