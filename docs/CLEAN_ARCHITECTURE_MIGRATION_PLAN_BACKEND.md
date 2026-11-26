# Backend Clean Architecture Migration Plan

## Goal and scope

Keep backend business rules independent of Django, SQLite, HTTP, and vector storage. Preserve the existing API contract while moving behavior out of views and commands into entities and use cases.

This plan covers the backend only. Follow [the frontend migration plan](CLEAN_ARCHITECTURE_MIGRATION_PLAN_FRONTEND.md) for frontend structure.

## Dependency rules

The backend has four layers:

1. **Entities** hold framework-free business rules, such as challenge-tree validation, answer matching, star scoring, run transitions, and profile scoring.
2. **Use cases** coordinate one application goal using entities and ports. They do not import Django, ORM models, HTTP request/response classes, or adapter implementations.
3. **Adapters** translate HTTP and command input, implement ports with Django/SQLite/files/vectors, and present output as JSON or command results.
4. **Configuration** in `config/container.py` connects use cases to their adapters.

Dependencies point inward: adapters may import use cases and entities; use cases may import entities and port protocols; entities import neither.

Views and management commands should parse input, call a use case, and return its output. ORM queries, filesystem access, HTTP status mapping, and response formatting belong in adapters.

## One folder per use case

Every use case has its own directory under `useCases/`. Keep shared port protocols in the app's `useCases/ports.py`; do not put use-case interactors in that shared file.

For example:

```text
backend/
├── config/
│   └── container.py
├── play/
│   ├── domain/
│   │   ├── attempt.py
│   │   ├── run.py
│   │   ├── answerMatching.py
│   │   └── starRules.py
│   ├── useCases/
│   │   ├── ports.py
│   │   ├── manageChallengeRun/
│   │   │   ├── Interactor.py
│   │   │   ├── InputBoundary.py
│   │   │   ├── InputData.py
│   │   │   ├── OutputBoundary.py
│   │   │   └── OutputData.py
│   │   └── recordChallengeAttempt/
│   │       ├── Interactor.py
│   │       ├── InputBoundary.py
│   │       ├── InputData.py
│   │       ├── OutputBoundary.py
│   │       └── OutputData.py
│   ├── adapters/
│   │   ├── manageChallengeRun/
│   │   │   ├── Controller.py
│   │   │   └── Presenter.py
│   │   ├── recordChallengeAttempt/
│   │   │   ├── Controller.py
│   │   │   └── Presenter.py
│   │   ├── repositories.py
│   │   ├── unitOfWork.py
│   │   └── vectorToneMatcher.py
│   └── models.py
└── challenges/
    └── ...
```

Use camelCase folder names, including the `useCases/` package and each use-case folder named for its use case. Inside a use-case folder, name each file for its role in PascalCase (`Interactor.py`, `InputData.py`, `OutputBoundary.py`) without repeating the use-case name. Other modules use camelCase, including class-focused ones (`run.py`, `unitOfWork.py`, `vectorToneMatcher.py`). Tests are `test<Subject>.py` or `tests.py`, which Django's default `test*.py` discovery pattern finds, and management commands stay snake_case because Django uses the filename as the command name. Small use cases do not need empty boilerplate files; add only the pieces they use. App-wide ports and adapter implementations can be shared. See [CONTRIBUTING.md](CONTRIBUTING.md#backend-naming) for the repository-wide naming rule.

Use the same pattern in `challenges/useCases/` and `users/useCases/`. A use case must not be a standalone module directly under `useCases/`.

## App ownership

| App | Owns |
| --- | --- |
| `challenges/` | `Challenge` and `ConversationNode`; challenge browsing and metadata; package import and validation |
| `play/` | `Run`, `Attempt`, `AnswerMatching`, and `StarRules`; run lifecycle and attempt recording |
| `users/` | `Profile`; account sessions, groups, profile updates, leaderboard, and guest-run claims |
| `tone/` | Tone-vector model and loading command; vector data access used by the play tone-matcher adapter |
| `config/` | Django settings, root routes, and dependency composition |

Keep Django models and migrations at the app boundary. Repositories convert between ORM rows and domain entities. The play use case obtains challenges, attempts, profiles, runs, tone matching, and transactions through ports rather than importing their Django models.

## Use-case map

Create one directory per use case. These names describe application goals; several goals may be reached through related URLs or commands.

- **Challenges:** `browseChallenges`, `getChallenge`, `importChallengePackage`, `validateChallenges`
- **Play:** `manageChallengeRun`, `recordChallengeAttempt`
- **Users:** `signUp`, `logIn`, `logOut`, `getCurrentUser`, `listGroups`, `viewProfile`, `updateProfile`, `getLeaderboard`, `claimGuestAttempt`

`viewProfile` and `updateProfile` are migrated, with per-use-case input/output boundaries, controllers, presenters, and container wiring. `viewProfile` is the implementation name for the former `getProfile` goal and covers both public profile read routes, preserving each response schema. `updateProfile` receives typed editable details after the controller handles JSON parsing and field selection; the interactor owns authorization, email-format validation, unique-team selection, and the account/profile transaction. Shared framework-free rules live in `users/domain/profileChanges.py`. Profile security corrections explicitly restrict writes to account details, reject score/total/login-history fields, and remove email from public responses. The domain `Profile` is the single home for score and login-day mutation rules; ORM helpers and unused auth/group ports have been removed. Numeric profile and claim presenters share a progress serializer. See `users/testProfileUseCases.py` and `users/testProfileDomain.py` for fake-port and entity tests, and `users/testProfileAPI.py` for rejection, privacy, and rollback coverage.

The run workflow covers starting a run, reading its snapshot, grading tone and action answers, selecting responses, and advancing the conversation. Keep these operations together only while they share a clear run boundary and coherent input/output contract.

Root and health status, CSRF token issuance, and static media serving are transport or infrastructure concerns; they do not need artificial use-case folders. Loading vector data is a management command, not a player-facing use case.

## Migration sequence

1. **Keep contracts stable.** Use the existing endpoint documentation and relevant backend tests to capture request, response, status, and persistence behavior before changing a route.
2. **Move one use case at a time.** Add its domain rules and port protocols, then create its dedicated `useCases/<name>/` directory and interactor.
3. **Add adapters and wiring.** Implement repository, matcher, or file ports; add the controller and presenter; register the dependencies in `config/container.py`. Keep the view or command limited to input parsing and dispatch.
4. **Preserve transaction boundaries.** Lock and revalidate state when needed. Changes that make up one completion, such as the run state, attempt history, and profile score, must commit or roll back together.
5. **Remove duplicate behavior.** Once the use case owns a rule, delete its old view/client copy when the API migration allows it. Update `docs/ARCHITECTURE.md` when routes, ownership, or directories change.

Migrate challenges, play, and users independently where their ports allow it. Keep API and database changes explicit; add migrations only when the stored schema changes.

## Completion criteria

A use case is complete when:

- Its application code lives in its own `useCases/<name>/` directory.
- Its interactor depends only on entities and port protocols.
- Django views and commands contain no business rules or direct ORM access for that use case.
- Its presenter preserves the documented response shape and status behavior.
- Unit tests exercise the interactor with fake ports, and endpoint tests cover the adapter contract.
- Any related route or structural change is documented in `docs/ARCHITECTURE.md`.
