# API Endpoints

## Challenges

### `GET /api/challenges/<slug>/`

Returns public metadata for one challenge. Unknown slugs return
`{"detail":"Challenge not found."}` with status 404.

```json
{
  "name": "<challenge name>",
  "slug": "<challenge slug>",
  "challenge_date": "<YYYY-MM-DD>",
  "difficulty": 1,
  "category": "<category>"
}
```

### `GET /api/challenges/?category=<category>&date=<YYYY-MM-DD>&difficulty=<1-5>&name=<text>`

All filters are optional. Category, date, and difficulty match strictly; name
uses fuzzy matching. The response is an object containing matching challenge
summaries (an empty array when none match):

```json
{
  "challenges": [
    {
      "name": "<challenge name>",
      "slug": "<challenge slug>",
      "challenge_date": "<YYYY-MM-DD>",
      "difficulty": 1,
      "category": "<category>"
    }
  ]
}
```

Invalid filter values return status 400 and a `detail` string, for example
`{"detail":"Invalid category filter."}`.

### `POST /api/challenges/<slug>/attempts/`

Send an empty JSON object (`{}`). A successful response has status 201 and
returns the opening run snapshot. The challenge must have a conversation tree.

```json
{
  "attempt_id": "<UUID>",
  "stage": "tone",
  "challenge": {
    "name": "<challenge name>",
    "slug": "<challenge slug>",
    "challenge_date": "<YYYY-MM-DD>",
    "difficulty": 1,
    "category": "<category>"
  },
  "opening": {
    "id": "<node key>",
    "type": "question",
    "transcript_url": "media/<relative transcript path>",
    "audio_url": "media/<relative audio path>"
  },
  "conversation": [],
  "choices": [],
  "tone_correct": null,
  "tone_time": null,
  "tone_speed_correct": null
}
```

An unknown challenge returns status 404 with
`{"detail":"Challenge not found."}`. The `attempt_id` is used by the attempt
endpoints below. Transcript and audio contents are fetched from the returned
media URLs.

## Attempts

Every attempt endpoint uses the run snapshot shown here. Node `type` is
`question` or `response`. `choices` contain response nodes that can currently
be selected. The `tone_similarity` field appears after tone grading; completion
fields appear only when `stage` is `completed`.

```json
{
  "attempt_id": "<UUID>",
  "stage": "<tone | conversation | action | completed>",
  "challenge": {
    "name": "<challenge name>",
    "slug": "<challenge slug>",
    "challenge_date": "<YYYY-MM-DD>",
    "difficulty": 1,
    "category": "<category>"
  },
  "opening": {
    "id": "<node key>",
    "type": "question",
    "transcript_url": "media/<relative transcript path>",
    "audio_url": "media/<relative audio path>"
  },
  "conversation": [
    {
      "id": "<node key>",
      "type": "<question | response>",
      "transcript_url": "media/<relative transcript path>",
      "audio_url": "media/<relative audio path>"
    }
  ],
  "choices": [
    {
      "id": "<node key>",
      "type": "response",
      "transcript_url": "media/<relative transcript path>",
      "audio_url": "media/<relative audio path>",
      "choice_id": "<zero-based index as a string>"
    }
  ],
  "tone_correct": null,
  "tone_time": null,
  "tone_speed_correct": null,
  "tone_similarity": 0.85,
  "action_correct": true,
  "score": 2,
  "required_action": "<string; present when completed>",
  "completed_at": "<ISO-8601 timestamp>"
}
```

Before tone grading, the three tone result fields are `null` and
`tone_similarity` is omitted. After grading, `tone_correct` and
`tone_speed_correct` are booleans and `tone_time`/`tone_similarity` are numbers.
The four completion fields are omitted until the run is completed.

### `GET /api/attempts/<uuid>/`

Returns the current run snapshot. Unknown IDs return status 404 with
`{"detail":"Attempt not found."}`. A run owned by another signed-in account
returns status 403 with a `detail` string.

### `POST /api/attempts/<uuid>/tone/`

Request:

```json
{
  "answer": "<tone guess>"
}
```

Returns the snapshot after tone grading, with `stage` set to `conversation` and
the current response choices. Invalid JSON or answer shape returns status 400;
an unknown answer word returns 422; a missing attempt returns 404; unavailable
tone vectors return 503. Errors use `{"detail":"<message>"}`.

### `POST /api/attempts/<uuid>/choices/`

Request (use a `choice_id` from the current snapshot):

```json
{
  "choice_id": "<zero-based index as a string>"
}
```

Returns the updated snapshot, including the selected response and any follow-up
question in `conversation`, and the next available choices. Invalid choice or
body returns status 400; an invalid stage transition returns 409. Errors use a
`detail` string.

### `POST /api/attempts/<uuid>/continue/`

Send `{}` after there are no choices left. Returns the snapshot with
`stage: "action"`. Invalid body or remaining choices return status 400; an
invalid stage transition returns 409. Errors use a `detail` string.

### `POST /api/attempts/<uuid>/action/`

Request:

```json
{
  "answer": "<action answer>"
}
```

Returns the completed run snapshot, including `action_correct`, `score`,
`required_action`, and `completed_at`. Invalid body returns status 400; an
invalid stage transition returns 409. Errors use a `detail` string. Completing
a user-bound run also records it on that user's profile.

## Users and profiles

### `GET /api/users/<username>/`

Returns the requested user's profile:

```json
{
  "slug": "<username>",
  "challenge_scores": {
    "<challenge slug>": 2
  },
  "total_score": 2.0,
  "name": "<full name or username>",
  "team": "<team slug or empty string>",
  "login_days": ["<YYYY-MM-DD>"],
  "avatar": "fox",
  "email": "<email or empty string>"
}
```

Avatar values are `fox`, `owl`, `bear`, `cat`, `robot`, and `ghost`. A missing
user returns status 404 with a `detail` string.

### `POST /api/users/<username>/`

Updates the signed-in user's own profile. The request may include any subset of
the fields in the GET response. `slug`, if supplied, must match the URL;
`total_score` must equal the sum of `challenge_scores`. The successful response
is the same profile object shown above. Anonymous requests return 401, attempts
to update another user's profile return 403, and invalid input returns 400;
errors use `{"detail":"<message>"}`.

### `GET /api/users/leaderboard/`

Returns up to ten profiles ordered by score:

```json
{
  "leaderboard": [
    {
      "user_id": 12,
      "username": "<username>",
      "avatar": "fox",
      "total_score": 2
    }
  ]
}
```

### `GET /api/users/<user_id>/profile/`

Returns public score and progress data:

```json
{
  "user_id": 12,
  "username": "<username>",
  "avatar": "fox",
  "total_score": 2,
  "completed_challenges": 1,
  "scores": {
    "<challenge slug>": 2
  }
}
```

A missing user ID returns status 404 with a `detail` string.

### `POST /api/users/me/scores/<challenge_slug>/`

Claim a completed run for the signed-in user. Request:

```json
{
  "attempt_id": "<UUID>"
}
```

Returns the public profile progress object above, with an additional `attempt`:

```json
{
  "user_id": 12,
  "username": "<username>",
  "avatar": "fox",
  "total_score": 2,
  "completed_challenges": 1,
  "scores": {
    "<challenge slug>": 2
  },
  "attempt": {
    "attempt_id": "<UUID>",
    "challenge_slug": "<challenge slug>",
    "score": 2,
    "completed_at": "<ISO-8601 timestamp>"
  }
}
```

New claims return status 201; repeated claims return 200. Anonymous requests
return 401; missing, mismatched, incomplete, or conflicting runs return an
appropriate 400, 404, or 409 response with a `detail` string.

## Authentication

### `GET /api/users/auth/csrf/`

Also sets the CSRF cookie.

```json
{
  "csrfToken": "<token>"
}
```

### `POST /api/users/auth/signup/`

Request requires `username` and `password`; `email` and `group_id` are optional.
`group_id` must be a positive integer or `null`. On success, status 201 signs
the new user in and returns:

```json
{
  "user": {
    "id": 12,
    "username": "<username>",
    "email": "<email or empty string>"
  },
  "csrfToken": "<token>"
}
```

Invalid signup data returns status 400 with an `errors` object keyed by field,
or a `detail` string for malformed requests.

### `POST /api/users/auth/login/`

Request:

```json
{
  "username": "<username>",
  "password": "<password>"
}
```

On success returns the same user-and-token object as signup. Invalid credentials
return status 401 with `{"detail":"Invalid username or password."}`.

### `POST /api/users/auth/logout/`

Ends the current session and returns:

```json
{
  "detail": "Logged out."
}
```

### `GET /api/users/auth/me/`

Returns the same user-and-token object as signup for an authenticated session.
Otherwise returns status 401 with
`{"detail":"Authentication required."}`.

### `GET /api/users/groups/`

Returns groups available during signup (the array can be empty):

```json
{
  "groups": [
    {
      "id": 3,
      "name": "<group name>"
    }
  ]
}
```

## Media files (development)

When Django `DEBUG` is enabled, `/media/<path>` serves files from the media
directory. Challenge snapshots return the transcript and audio paths as URLs;
the transcript and audio responses are file contents rather than JSON objects.

## Not separate API endpoints

- `POST /api/users/<username>/add_challenge` is not implemented. Scores are
  recorded on run completion or by claiming a guest run through
  `POST /api/users/me/scores/<challenge_slug>/`.
- There is no standalone tone similarity endpoint; tone grading is part of
  `POST /api/attempts/<uuid>/tone/`.
