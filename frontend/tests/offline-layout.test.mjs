import assert from 'node:assert/strict'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { build } from 'vite'
import react from '@vitejs/plugin-react'

// Bundle JSX in memory with the existing build tools; share React with the renderer.
const bundle = await build({
  configFile: false,
  logLevel: 'silent',
  plugins: [
    {
      name: 'external-test-react',
      enforce: 'pre',
      resolveId(id) {
        if (id === 'react' || id.startsWith('react/')) {
          return { id: import.meta.resolve(id), external: true }
        }
      },
      transform(code, id) {
        if (id === fileURLToPath(new URL('../src/app.tsx', import.meta.url))) {
          return {
            code: `${code}\nexport { default as ResultsPage } from './pages/resultsPage';`,
            map: null,
          }
        }
      },
    },
    react(),
  ],
  build: {
    write: false,
    minify: false,
    lib: {
      entry: fileURLToPath(new URL('../src/app.tsx', import.meta.url)),
      formats: ['es'],
    },
  },
})
const output = (Array.isArray(bundle) ? bundle : [bundle])
  .flatMap((result) => result.output)
  .find((item) => item.type === 'chunk' && item.isEntry)
const { default: App, ResultsPage } = await import(
  `data:text/javascript;base64,${Buffer.from(output.code).toString('base64')}`
)

function renderPage(t, pathname) {
  const originalWindow = globalThis.window
  globalThis.window = {
    location: { pathname },
    sessionStorage: { getItem: () => null },
  }
  t.after(() => {
    globalThis.window = originalWindow
  })
  return renderToStaticMarkup(createElement(App))
}

test('home renders its calendar immediately without backend data', (t) => {
  const html = renderPage(t, '/')
  for (const day of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']) {
    assert.ok(html.includes(day))
  }
  assert.match(html, /Daily recording/)
  assert.match(html, /Connecting to recordings and account services/)
  assert.doesNotMatch(html, /Start challenge|Begin →|Recording unavailable/)
  // Calendar actions stay disabled until a real recording is available.
  const buttons = html.match(/<button\b[^>]*>/g) ?? []
  const isMonthNav = (button) =>
    /aria-label="(Previous|Next) month"/.test(button)
  const dayCells = buttons.filter((button) => !isMonthNav(button))
  assert.ok(dayCells.length >= 28)
  assert.ok(dayCells.every((button) => button.includes('disabled')))
  // Month navigation is always available.
  assert.equal(buttons.filter(isMonthNav).length, 2)
})

test('login and signup forms remain visible while the session request is pending', (t) => {
  const login = renderPage(t, '/login')
  assert.match(login, /Welcome back/)
  assert.match(login, /name="username"/)
  assert.match(login, /name="password"/)
  assert.doesNotMatch(login, /name="group_id"/)
  assert.match(login, /Checking account…/)
  const signup = renderPage(t, '/signup')
  assert.match(signup, /Create an account/)
  assert.match(signup, /name="email"/)
  assert.match(signup, /name="confirmation"/)
  assert.match(signup, /<select[^>]*name="group_id"/)
})

test('a direct profile visit shows the login form while the account is unknown', (t) => {
  const html = renderPage(t, '/profile')
  assert.match(html, /name="username"/)
  assert.doesNotMatch(html, /Account unavailable/)
})

test('a direct slug URL starts the challenge before summaries load', (t) => {
  const html = renderPage(t, '/challenges/charged-twice')
  assert.match(html, /Checking your account before starting the challenge/)
})

test('a direct results URL renders the results shell before storage loads', (t) => {
  const html = renderPage(t, '/challenges/charged-twice/complete')
  assert.match(html, /Loading your result/)
})

test('results distinguish saving, saved, retryable failure, guests, and another account', () => {
  const claim = (overrides = {}) => ({
    status: 'saving',
    message: 'Saving your score…',
    showLogin: false,
    showProfile: false,
    canRetry: false,
    ...overrides,
  })
  const props = {
    viewModel: {
      status: 'ready',
      challengeName: 'Test recording',
      dateLabel: 'Thursday, October 15, 2026',
      heading: 'Beautifully handled.',
      starCount: 3,
      stars: [true, true, true],
      achievements: [
        { earned: true, title: 'Read the tone', detail: 'Tone matched.' },
        { earned: true, title: 'Quick instinct', detail: 'Fast.' },
        { earned: true, title: 'Correct next step', detail: 'Reset.' },
      ],
    },
    claimViewModel: claim(),
    onHome() {},
    onRetry() {},
    onRetryClaim() {},
    onLogin() {},
    onProfile() {},
  }
  const render = (extra) =>
    renderToStaticMarkup(createElement(ResultsPage, { ...props, ...extra }))
  assert.match(render(), /Saving your score/)
  assert.match(
    render({
      claimViewModel: claim({
        status: 'saved',
        message: 'Score saved to your profile. Your best score counts.',
        showProfile: true,
      }),
    }),
    /Score saved to your profile/,
  )
  const failed = render({
    claimViewModel: claim({
      status: 'error',
      message: 'Could not save your score. Backend unavailable.',
      canRetry: true,
    }),
  })
  assert.match(failed, /Retry saving/)
  assert.doesNotMatch(failed, /Score saved to your profile/)
  assert.match(
    render({
      claimViewModel: claim({
        status: 'guest',
        message: 'Your result is kept in this browser session.',
        showLogin: true,
      }),
    }),
    /Log in to save your score/,
  )
  assert.match(
    render({
      claimViewModel: claim({
        status: 'other-account',
        message:
          'This result belongs to another session. Retry the challenge to save a score to this account.',
      }),
    }),
    /another session/,
  )
})

test('results render loading and unavailable states', () => {
  const props = {
    viewModel: { status: 'loading', message: 'Loading your result…' },
    claimViewModel: {
      status: 'checking',
      message: 'Checking your account before saving…',
      showLogin: false,
      showProfile: false,
      canRetry: false,
    },
    onHome() {},
    onRetry() {},
    onRetryClaim() {},
    onLogin() {},
    onProfile() {},
  }
  const loading = renderToStaticMarkup(createElement(ResultsPage, { ...props }))
  assert.match(loading, /Loading your result/)
  const unavailable = renderToStaticMarkup(
    createElement(ResultsPage, {
      ...props,
      viewModel: {
        status: 'unavailable',
        message: 'This result is no longer available.',
      },
    }),
  )
  assert.match(unavailable, /no longer available/)
  assert.match(unavailable, /Back to calendar/)
})
