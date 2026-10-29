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
        if (id === fileURLToPath(new URL('../src/App.tsx', import.meta.url))) {
          return {
            code: `${code}\nexport { default as ResultsPage } from './pages/ResultsPage';`,
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
      entry: fileURLToPath(new URL('../src/App.tsx', import.meta.url)),
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
  assert.ok(buttons.length >= 28)
  assert.ok(buttons.every((button) => button.includes('disabled')))
})

test('login and signup forms remain visible while the session request is pending', (t) => {
  const login = renderPage(t, '/login')
  assert.match(login, /Welcome back/)
  assert.match(login, /name="username"/)
  assert.match(login, /name="password"/)
  assert.match(login, /Checking account…/)
  const signup = renderPage(t, '/signup')
  assert.match(signup, /Create an account/)
  assert.match(signup, /name="email"/)
  assert.match(signup, /name="confirmation"/)
})

test('a direct profile visit shows the login form while the account is unknown', (t) => {
  const html = renderPage(t, '/profile')
  assert.match(html, /name="username"/)
  assert.doesNotMatch(html, /Account unavailable/)
})

test('results distinguish saving, saved, retryable failure, guests, and another account', () => {
  const props = {
    challenge: {
      id: 42,
      name: 'Test recording',
      challenge_date: '2026-10-15',
      tone: 'calm',
      required_action: 'reset password',
    },
    result: {
      challengeId: 42,
      attemptId: '627e5d91-c343-44ae-b6ab-532b2ed41b8e',
      completedAt: '2026-10-29T01:23:45.000Z',
      toneCorrect: true,
      toneTime: 8,
      actionCorrect: true,
      userId: 7,
    },
    user: { id: 7, username: 'ada', email: '' },
    sessionLoading: false,
    onHome() {},
    onRetry() {},
    onSaveRetry() {},
    onLogin() {},
    onProfile() {},
  }
  const render = (extra) =>
    renderToStaticMarkup(createElement(ResultsPage, { ...props, ...extra }))
  assert.match(render({ saveState: { status: 'saving' } }), /Saving your score/)
  assert.match(
    render({ saveState: { status: 'saved' } }),
    /Score saved to your profile/,
  )
  const failed = render({
    saveState: { status: 'error', message: 'Backend unavailable.' },
  })
  assert.match(failed, /Retry saving/)
  assert.doesNotMatch(failed, /Score saved to your profile/)
  assert.match(
    render({ user: null, saveState: { status: 'saving' } }),
    /Log in to save your score/,
  )
  assert.match(
    render({ user: { id: 9 }, saveState: { status: 'saved' } }),
    /another session/,
  )
})
