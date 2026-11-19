import assert from 'node:assert/strict'
import test from 'node:test'
import {
  buildCredentials,
  passwordsMatch,
} from '../src/entities/authCredentials.ts'
import { AuthenticateUserInteractor } from '../src/auth/useCases/authenticateUser/authenticateUserInteractor.ts'
import { LoadSignupGroupsInteractor } from '../src/auth/useCases/loadSignupGroups/loadSignupGroupsInteractor.ts'
import { LogoutUserInteractor } from '../src/auth/useCases/logoutUser/logoutUserInteractor.ts'
import { RestoreSessionInteractor } from '../src/auth/useCases/restoreSession/restoreSessionInteractor.ts'

const user = { id: 7, username: 'ada', email: 'ada@example.com' }

const recorder = () => {
  const outputs = []
  return {
    outputs,
    boundary: {
      present(output) {
        outputs.push(output)
      },
    },
  }
}

test('auth credentials validate confirmation and normalize signup fields', () => {
  assert.equal(passwordsMatch('a', 'a'), true)
  assert.equal(passwordsMatch('a', 'b'), false)
  assert.deepEqual(
    buildCredentials({
      mode: 'login',
      username: ' ada ',
      email: 'ignored@example.com',
      password: 'secret',
      confirmation: 'secret',
      groupId: '3',
    }),
    { username: 'ada', password: 'secret' },
  )
  assert.deepEqual(
    buildCredentials({
      mode: 'signup',
      username: ' ada ',
      email: ' ada@example.com ',
      password: 'secret',
      confirmation: 'secret',
      groupId: '3',
    }),
    {
      username: 'ada',
      password: 'secret',
      email: 'ada@example.com',
      group_id: 3,
    },
  )
})

test('restoreSession presents the account or an anonymous session', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new RestoreSessionInteractor(
    {
      async restoreSession() {
        return user
      },
    },
    boundary,
  )
  await interactor.execute({ signal: new AbortController().signal })
  assert.deepEqual(outputs[0], { status: 'ready', user })

  const anonymous = recorder()
  const anonymousInteractor = new RestoreSessionInteractor(
    {
      async restoreSession() {
        return null
      },
    },
    anonymous.boundary,
  )
  await anonymousInteractor.execute({
    signal: new AbortController().signal,
  })
  assert.deepEqual(anonymous.outputs[0], { status: 'ready', user: null })
})

test('restoreSession reports account failures', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new RestoreSessionInteractor(
    {
      async restoreSession() {
        throw new Error('session unavailable')
      },
    },
    boundary,
  )
  await interactor.execute({ signal: new AbortController().signal })
  assert.deepEqual(outputs[0], {
    status: 'error',
    message: 'session unavailable',
  })
})

test('authenticateUser passes the action and credentials to the gateway', async () => {
  const { outputs, boundary } = recorder()
  const calls = []
  const interactor = new AuthenticateUserInteractor(
    {
      async authenticate(action, credentials, signal) {
        calls.push({ action, credentials, signal })
        return user
      },
    },
    boundary,
  )
  const signal = new AbortController().signal
  await interactor.execute({
    action: 'signup',
    credentials: { username: 'ada', password: 'secret' },
    signal,
  })
  assert.deepEqual(calls, [
    {
      action: 'signup',
      credentials: { username: 'ada', password: 'secret' },
      signal,
    },
  ])
  assert.deepEqual(outputs[0], { status: 'ready', user })
})

test('authenticateUser reports invalid credentials and aborts', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new AuthenticateUserInteractor(
    {
      async authenticate() {
        throw new Error('Invalid username or password.')
      },
    },
    boundary,
  )
  await interactor.execute({
    action: 'login',
    credentials: { username: 'ada', password: 'wrong' },
    signal: new AbortController().signal,
  })
  assert.deepEqual(outputs[0], {
    status: 'error',
    message: 'Invalid username or password.',
  })

  const aborted = recorder()
  const controller = new AbortController()
  controller.abort()
  const abortedInteractor = new AuthenticateUserInteractor(
    {
      async authenticate() {
        assert.fail('should not authenticate an aborted request')
      },
    },
    aborted.boundary,
  )
  await abortedInteractor.execute({
    action: 'login',
    credentials: { username: 'ada', password: 'secret' },
    signal: controller.signal,
  })
  assert.equal(aborted.outputs.length, 0)
})

test('logoutUser reports success and failure', async () => {
  const success = recorder()
  const successInteractor = new LogoutUserInteractor(
    {
      async logout() {},
    },
    success.boundary,
  )
  await successInteractor.execute({})
  assert.deepEqual(success.outputs[0], { status: 'ready' })

  const failure = recorder()
  const failureInteractor = new LogoutUserInteractor(
    {
      async logout() {
        throw new Error('logout unavailable')
      },
    },
    failure.boundary,
  )
  await failureInteractor.execute({})
  assert.deepEqual(failure.outputs[0], {
    status: 'error',
    message: 'logout unavailable',
  })
})

test('loadSignupGroups presents groups and failures', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new LoadSignupGroupsInteractor(
    {
      async loadGroups() {
        return [{ id: 3, name: 'Alpha team' }]
      },
    },
    boundary,
  )
  await interactor.execute({ signal: new AbortController().signal })
  assert.deepEqual(outputs[0], {
    status: 'ready',
    groups: [{ id: 3, name: 'Alpha team' }],
  })

  const failure = recorder()
  const failureInteractor = new LoadSignupGroupsInteractor(
    {
      async loadGroups() {
        throw new Error('groups unavailable')
      },
    },
    failure.boundary,
  )
  await failureInteractor.execute({
    signal: new AbortController().signal,
  })
  assert.deepEqual(failure.outputs[0], {
    status: 'error',
    message: 'groups unavailable',
  })
})
