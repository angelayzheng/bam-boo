import assert from 'node:assert/strict'
import test from 'node:test'
import {
  getCurrentUser,
  loadProfile,
  loadSignupGroups,
  saveChallengeResult,
  signIn,
  signOut,
} from '../src/auth.ts'

const user = { id: 7, username: 'ada', email: 'ada@example.com' }
const credentials = { username: 'ada', password: 'River!Quartz7Maple' }
const basePath = '/api/users/auth/'

test('signup loads existing group choices with cancellation and no caching', async (t) => {
  const signal = new AbortController().signal
  const groups = [
    { id: 3, name: 'Alpha team' },
    { id: 8, name: 'Zeta team' },
  ]
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/users/groups/')
    assert.equal(options.credentials, 'same-origin')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.signal, signal)
    return Response.json({ groups })
  })
  assert.deepEqual(await loadSignupGroups(signal), groups)
})

test('completion sends result metrics with session cookies and CSRF to the current-user score endpoint', async (t) => {
  const signal = new AbortController().signal
  const result = {
    challengeId: 42,
    attemptId: '627e5d91-c343-44ae-b6ab-532b2ed41b8e',
    completedAt: '2026-10-29T01:23:45.000Z',
    toneCorrect: true,
    toneTime: 8,
    actionCorrect: true,
    userId: 7,
  }
  const profile = {
    user_id: 7,
    username: 'ada',
    avatar: 'fox',
    scores: { 42: 100 },
    total_score: 100,
    completed_challenges: 1,
  }
  const requests = []
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    requests.push(url)
    assert.equal(options.credentials, 'same-origin')
    assert.equal(options.signal, signal)
    if (url === `${basePath}csrf/`)
      return Response.json({ csrfToken: 'fresh-token' })
    assert.equal(url, '/api/users/me/scores/42/')
    assert.equal(options.method, 'POST')
    assert.equal(options.headers['X-CSRFToken'], 'fresh-token')
    assert.deepEqual(JSON.parse(options.body), {
      tone_correct: true,
      tone_time: 8,
      action_correct: true,
      attempt_id: '627e5d91-c343-44ae-b6ab-532b2ed41b8e',
      completed_at: '2026-10-29T01:23:45.000Z',
    })
    return Response.json(profile)
  })
  assert.deepEqual(await saveChallengeResult(result, signal), profile)
  assert.deepEqual(requests, [`${basePath}csrf/`, '/api/users/me/scores/42/'])
})

test('saving reports an expired login or backend failure and can be retried', async (t) => {
  const result = {
    challengeId: 42,
    attemptId: '627e5d91-c343-44ae-b6ab-532b2ed41b8e',
    completedAt: '2026-10-29T01:23:45.000Z',
    toneCorrect: false,
    toneTime: 20,
    actionCorrect: true,
  }
  let response = Response.json(
    { detail: 'Authentication required.' },
    { status: 401 },
  )
  let attempts = 0
  t.mock.method(globalThis, 'fetch', async (url) => {
    if (url === `${basePath}csrf/`) return Response.json({ csrfToken: 'token' })
    attempts += 1
    return response
  })
  await assert.rejects(
    saveChallengeResult(result, new AbortController().signal),
    /Authentication required/,
  )
  response = new Response('Unavailable', { status: 503 })
  await assert.rejects(
    saveChallengeResult(result, new AbortController().signal),
    /Could not connect/,
  )
  response = Response.json({ scores: { 42: 33 }, total_score: 33 })
  assert.equal(
    (await saveChallengeResult(result, new AbortController().signal))
      .total_score,
    33,
  )
  assert.equal(attempts, 3)
})

test('restores the current account using the session cookie without caching', async (t) => {
  const signal = new AbortController().signal
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, `${basePath}me/`)
    assert.equal(options.signal, signal)
    assert.equal(options.credentials, 'same-origin')
    assert.equal(options.cache, 'no-store')
    return Response.json({ user, csrfToken: 'token' })
  })
  assert.deepEqual(await getCurrentUser(signal), user)
})

test('an anonymous session is distinct from a failed session check', async (t) => {
  const mock = t.mock.method(globalThis, 'fetch', async () =>
    Response.json({ detail: 'Authentication required.' }, { status: 401 }),
  )
  assert.equal(await getCurrentUser(new AbortController().signal), null)
  mock.mock.mockImplementation(
    async () => new Response('Error', { status: 500 }),
  )
  await assert.rejects(
    getCurrentUser(new AbortController().signal),
    /Could not connect/,
  )
})

test('signup and login acquire CSRF tokens before sending credentials', async (t) => {
  for (const action of ['signup', 'login']) {
    const requests = []
    const signal = new AbortController().signal
    const payload = {
      ...credentials,
      ...(action === 'signup' ? { email: user.email, group_id: 3 } : {}),
    }
    const mock = t.mock.method(globalThis, 'fetch', async (url, options) => {
      requests.push(url)
      assert.equal(options.credentials, 'same-origin')
      assert.equal(options.signal, signal)
      if (url === `${basePath}csrf/`) {
        assert.equal(options.cache, 'no-store')
        return Response.json({ csrfToken: 'current-token' })
      }
      assert.equal(url, `${basePath}${action}/`)
      assert.equal(options.method, 'POST')
      assert.equal(options.headers['X-CSRFToken'], 'current-token')
      assert.equal(options.headers['Content-Type'], 'application/json')
      assert.deepEqual(JSON.parse(options.body), payload)
      return Response.json({ user, csrfToken: 'rotated-token' })
    })
    assert.deepEqual(await signIn(action, payload, signal), user)
    assert.deepEqual(requests, [`${basePath}csrf/`, `${basePath}${action}/`])
    mock.mock.restore()
  }
})

test('logout obtains a fresh token after login rotates the CSRF secret', async (t) => {
  let token = 'before-login'
  const actions = []
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(options.credentials, 'same-origin')
    if (url === `${basePath}csrf/`) return Response.json({ csrfToken: token })
    assert.equal(options.headers['X-CSRFToken'], token)
    actions.push(url)
    if (url === `${basePath}login/`) {
      token = 'after-login'
      return Response.json({ user, csrfToken: token })
    }
    assert.equal(url, `${basePath}logout/`)
    assert.equal(options.method, 'POST')
    return Response.json({ detail: 'Logged out.' })
  })
  await signIn('login', credentials)
  await signOut()
  assert.deepEqual(actions, [`${basePath}login/`, `${basePath}logout/`])
})

test('server validation and invalid credentials are shown as useful messages', async (t) => {
  let response = Response.json(
    {
      errors: {
        username: ['That username is taken.'],
        password: ['Too common.'],
      },
    },
    { status: 400 },
  )
  t.mock.method(globalThis, 'fetch', async (url) =>
    url === `${basePath}csrf/`
      ? Response.json({ csrfToken: 'token' })
      : response,
  )
  await assert.rejects(
    signIn('signup', credentials),
    /That username is taken. Too common./,
  )
  response = Response.json(
    { detail: 'Invalid username or password.' },
    { status: 401 },
  )
  await assert.rejects(
    signIn('login', credentials),
    /Invalid username or password/,
  )
})

test('HTML CSRF errors give a retry message rather than a JSON parsing error', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url) =>
    url === `${basePath}csrf/`
      ? Response.json({ csrfToken: 'token' })
      : new Response('<html>Forbidden</html>', { status: 403 }),
  )
  await assert.rejects(signOut(), /security token expired/)
})

test('a failed CSRF bootstrap prevents the mutation', async (t) => {
  const requests = []
  t.mock.method(globalThis, 'fetch', async (url) => {
    requests.push(url)
    return new Response('Unavailable', { status: 503 })
  })
  await assert.rejects(signIn('login', credentials), /Could not connect/)
  assert.deepEqual(requests, [`${basePath}csrf/`])
})

test('profile loads stored progress for the signed-in account with cancellation', async (t) => {
  const signal = new AbortController().signal
  const profile = {
    user_id: 7,
    avatar: 'fox',
    total_score: 80,
    completed_challenges: 1,
    scores: { 42: 80 },
  }
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/users/7/profile/')
    assert.equal(options.signal, signal)
    assert.equal(options.cache, 'no-store')
    return Response.json(profile)
  })
  assert.deepEqual(await loadProfile(7, signal), profile)
})

test('aborted session checks preserve cancellation', async (t) => {
  const controller = new AbortController()
  controller.abort()
  t.mock.method(globalThis, 'fetch', async (_url, { signal }) => {
    signal.throwIfAborted()
  })
  await assert.rejects(getCurrentUser(controller.signal), {
    name: 'AbortError',
  })
})
