import assert from 'node:assert/strict'
import test from 'node:test'
import { authApi } from '../src/auth/dataAccessInterface/authGatewayApi.ts'

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
  assert.deepEqual(await authApi.loadGroups(signal), groups)
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
  assert.deepEqual(await authApi.restoreSession(signal), user)
})

test('an anonymous session is distinct from a failed session check', async (t) => {
  const mock = t.mock.method(globalThis, 'fetch', async () =>
    Response.json({ detail: 'Authentication required.' }, { status: 401 }),
  )
  assert.equal(await authApi.restoreSession(new AbortController().signal), null)
  mock.mock.mockImplementation(
    async () => new Response('Error', { status: 500 }),
  )
  await assert.rejects(
    authApi.restoreSession(new AbortController().signal),
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
    assert.deepEqual(await authApi.authenticate(action, payload, signal), user)
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
  await authApi.authenticate('login', credentials)
  await authApi.logout()
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
    authApi.authenticate('signup', credentials),
    /That username is taken. Too common./,
  )
  response = Response.json(
    { detail: 'Invalid username or password.' },
    { status: 401 },
  )
  await assert.rejects(
    authApi.authenticate('login', credentials),
    /Invalid username or password/,
  )
})

test('HTML CSRF errors give a retry message rather than a JSON parsing error', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url) =>
    url === `${basePath}csrf/`
      ? Response.json({ csrfToken: 'token' })
      : new Response('<html>Forbidden</html>', { status: 403 }),
  )
  await assert.rejects(authApi.logout(), /security token expired/)
})

test('a failed CSRF bootstrap prevents the mutation', async (t) => {
  const requests = []
  t.mock.method(globalThis, 'fetch', async (url) => {
    requests.push(url)
    return new Response('Unavailable', { status: 503 })
  })
  await assert.rejects(
    authApi.authenticate('login', credentials),
    /Could not connect/,
  )
  assert.deepEqual(requests, [`${basePath}csrf/`])
})

test('aborted session checks preserve cancellation', async (t) => {
  const controller = new AbortController()
  controller.abort()
  t.mock.method(globalThis, 'fetch', async (_url, { signal }) => {
    signal.throwIfAborted()
  })
  await assert.rejects(authApi.restoreSession(controller.signal), {
    name: 'AbortError',
  })
})
