# bam-boo! Clean Architecture Migration Proposal

**bam-boo!** works and is well tested, but its business rules are spread across Django views and React pages. This proposal moves them into a framework-free backend core organized as **6 entities**, **15 use cases**, and **6 vertical slices**, with Django, SQLite, and the media files kept at the edges.

## The Codebase at a Glance

**bam-boo!** is a daily training game for contact-centre agents: hear a customer, name their tone, choose replies through a branching conversation, then pick the next action, for up to 3 stars.

* **Backend Stack:** Django returning JSON; one SQLite file for all data; MP3s and transcripts in a `media/` folder.

### How the Backend Is Organized Today

| Path | Contents | 
| ----- | ----- | 
| **`backend/`** |  | 
| `challenges/` | Challenge model, list/detail API, package import + validation | 
| `tone/` | Word vectors + tone-grading endpoint | 
| `users/` | Profiles, attempts, auth, score saving | 
| `config/` | Settings, root URLs | 

* **How a request flows:** Client calls `/api/..` $\rightarrow$ a URL maps to one view function $\rightarrow$ that function parses the request, applies the rules, queries SQLite through the ORM, and builds the JSON.

* **What works well:** Apps split by feature, thorough validation, about 1,500 lines of backend tests, and CI running tests, formatting, lint, and the build.

### What Blocks Growth

* **No layers.** Each view does parsing, rules, database access, and response building at once.

* **Rules in two places.** Star scoring lives in both a Django view and the client; action matching runs only in the browser.

* **Rules with no owner.** The server trusts the client's own grading, the challenge response sends the answers to the browser, and users can write their own scores.

* **Storage leaks everywhere.** Every view queries the ORM directly, and file paths are built inline.

* **Features shown but not built.** The streak is hardcoded and the leaderboard link goes nowhere.

## Clean Architecture for bam-boo!

The target has **four layers**. The business rules sit in the middle and depend on nothing; Django, SQLite, and the media files sit at the edge and can be swapped without touching the rules.

### Four-Layer Architecture Overview

> *Dependencies point inward: each layer only knows the layers below it; entities know nothing else.*

```
flowchart TB
    subgraph L4["4. Frameworks and drivers (tools we plug in; can be swapped)"]
        F1[Django + admin]
        F2[SQLite via ORM]
        F3[media/ audio + text]
        F4[Numberbatch vectors]
    end

    subgraph L3["3. Interface adapters (translate between the core and the tools)"]
        A1[Controllers]
        A2[Presenters]
        A3[ORM repositories]
        A4[File media store]
        A5[Vector tone matcher]
    end

    subgraph L2["2. Use cases (15 user goals, plus the ports they need)"]
        U1[Challenges · 2]
        U2["Play · 2 (core)"]
        U3[Accounts · 5]
        U4[Progress · 4]
        U5[Content · 2]
        U6["Ports (interfaces)"]
    end

    subgraph L1["1. Entities (6 business objects and all the rules)"]
        E1[Challenge]
        E2[ConversationNode]
        E3[Attempt]
        E4[Profile]
        E5[StarRules]
        E6[AnswerMatching]
    end

    L4 --> L3 --> L2 --> L1


```

The **ports** in the use case layer are interfaces such as `ChallengeRepository` or `ToneMatcher`. The **adapters** one layer up implement them with the ORM, the file system, and the word vectors, which is how storage ends up *"behind clean interfaces"* as the team's brief asks.

## One Use Case, End to End

The diagram below follows the CSC207 Clean Architecture scenario layout for the core use case, `CompleteChallenge`. Every other use case follows the same shape with its own classes.

> *Note: Unprefixed boxes are `CompleteChallenge` classes (e.g., `Controller` = `CompleteChallengeController`). Dependencies point inward: frameworks to adapters to use case to entities, never the other way.*

```
flowchart LR
    subgraph Adapters["Interface adapters"]
        Controller["[C] Controller<br/>play/adapters/views.py"]
        Presenter["[C] Presenter<br/>builds JSON + status"]
        ViewModel["[C] ViewModel<br/>JSON response payload"]
    end

    subgraph UseCases["Application business rules"]
        InputData["[C] InputData<br/>answers, time, ids"]
        InputBoundary["[I] InputBoundary<br/>execute(input)"]
        Interactor["[C] Interactor<br/>play/use_cases/"]
        OutputBoundary["[I] OutputBoundary<br/>success / errors"]
        OutputData["[C] OutputData<br/>stars, total, saved"]
        DataAccessI["[I] Data access<br/>ChallengeRepository<br/>AttemptRepository<br/>ToneMatcher"]
    end

    subgraph EntitiesLayer["Enterprise rules"]
        Entities["[C] Entities<br/>Challenge, Attempt,<br/>StarRules, AnswerMatching,<br/>Profile"]
    end

    subgraph Frameworks_DB["Frameworks and drivers"]
        DataAccessC["[C] Data access<br/>DjangoChallengeRepository<br/>DjangoAttemptRepository<br/>VectorToneMatcher"]
        DB["Database<br/>SQLite + word vectors"]
    end

    Controller -->|creates| InputData
    Controller -->|calls| InputBoundary
    Interactor -.->|implements| InputBoundary
    Interactor -->|uses| InputData
    Interactor -->|uses| Entities
    Interactor -->|calls| DataAccessI
    Interactor -->|creates| OutputData
    Interactor -->|calls| OutputBoundary
    Presenter -.->|implements| OutputBoundary
    Presenter -->|uses| OutputData
    Presenter -->|builds| ViewModel
    DataAccessC -.->|implements| DataAccessI
    DataAccessC -->|uses| Entities
    DataAccessC -->|queries| DB


```

A request runs:

`Controller` $\rightarrow$ `InputData` $\rightarrow$ `Interactor`, which applies the entity rules, saves through the data access interfaces, and hands `OutputData` to the `Presenter`, which builds the `ViewModel` returned as JSON.

It uses five of the six entities: `ConversationNode` belongs to `Challenge` and only matters when importing challenges.

## File Structure

Each backend app gets the same three folders, one per inner layer, and Django's own files stay as the outer layer. A new `play/` app holds the grading and scoring that today is split between `users/`, `tone/`, and the client.

```
backend/
├── config/
│   └── container.py            # composition root: builds each use case with its adapters
├── challenges/                 # (same shape in play/ and users/)
│   ├── domain/                 # entities + rules, no Django imports
│   ├── use_cases/              # one file per use case + ports.py (interfaces)
│   ├── adapters/
│   │   ├── views.py            # controllers: parse request, call use case
│   │   ├── presenters.py       # JSON + status codes
│   │   ├── repositories.py     # ORM implementations of the ports
│   │   └── media_store.py      # file-system implementation (challenges only)
│   ├── models.py               # Django ORM models
│   └── admin.py, management/   # Django admin + CLI commands (call use cases)
├── play/                       # new: CompleteChallenge, GradeTone, scoring rules
└── tone/                       # storage only: word-vector model, load command, VectorToneMatcher


```

### Which App Holds What

Each backend app is a feature area: it groups related use cases with the entities they own. Apps are folders; slices (below) are units of work, so one slice can touch two apps.

| App | Use cases | Entities it owns | 
| ----- | ----- | ----- | 
| **`challenges/`** | `BrowseChallenges`, `GetChallengeForPlay`, `ImportChallengePackage`, `ValidateChallenges` | `Challenge`, `ConversationNode` | 
| **`play/` (new)** | `GradeTone`, `CompleteChallenge` | `Attempt`, `StarRules`, `AnswerMatching` | 
| **`users/`** | `SignUp`, `LogIn`, `LogOut`, `GetCurrentUser`, `ListGroups`, `ViewProfile`, `UpdateProfile`, `ViewLeaderboard`, `RecordDailyLogin` | `Profile` | 
| **`tone/`** | *none: storage only* | *none (word vectors are data, used by `VectorToneMatcher`)* | 

### How Use Cases Share Code

Each use case gets its own path from request to response. Use cases in the same app share what sits on either side of that path: the entities on the inside and the database access on the outside.

| Piece | Own or shared? | Example in `challenges/` | 
| ----- | ----- | ----- | 
| **Controller** | **Own:** one per use case | One view function each for Browse, GetForPlay, Import, Validate | 
| **InputData, OutputData** | **Own** | Each use case takes and returns different data | 
| **Interactor + boundaries** | **Own** | `browse_challenges.py`, `get_challenge_for_play.py`, ... | 
| **Presenter, ViewModel** | **Own** *(may reuse a small JSON helper)* | Each response has a different shape | 
| **Entities** | **Shared** within the app | All four use `Challenge` | 
| **Data access interface** | **Shared:** one per entity, not per use case | One `ChallengeRepository` with `list()`, `get_by_slug()`, `save()` | 
| **Data access implementation** | **Shared** | One `DjangoChallengeRepository` class | 
| **Wiring** | **Shared** by the whole project | `config/container.py` builds every use case | 

#### Example Breakdown in `challenges/`

```
challenges/
├── domain/
│   └── challenge.py                 # Challenge, ConversationNode         <- shared
├── use_cases/
│   ├── ports.py                     # ChallengeRepository, MediaStore   <- shared
│   ├── browse_challenges.py         # its own interactor, input/output data, boundaries
│   ├── get_challenge_for_play.py    # its own
│   ├── import_challenge_package.py  # its own
│   └── validate_challenges.py       # its own
└── adapters/
    ├── repositories.py              # DjangoChallengeRepository         <- shared
    ├── media_store.py               # FileMediaStore                    <- shared
    ├── views.py                     # one controller per use case
    └── presenters.py                # one presenter per use case


```

Across apps, use cases only meet through interfaces. `CompleteChallenge` in `play/` needs a challenge's answers, which belong to `challenges/`. So `play/` asks for the `ChallengeRepository` interface and never imports the Django `Challenge` model; `config/container.py` plugs in the real class. Each app can then change how it stores data without breaking the others.

> **In one sentence:** Each use case owns its controller, interactor, and presenter; use cases in the same app share entities and repositories; different apps talk only through interfaces.

### What Moves Where

| Currently | Would move to | 
| ----- | ----- | 
| Rules inside `views.py` (stars, idempotency, best score) | `domain/` + `use_cases/` | 
| Tone similarity in `tone/views.py` | `play/domain/` + a tone-matcher adapter | 
| `Model.objects...` calls inside views | `adapters/repositories.py` | 
| `MEDIA_ROOT` paths in `importer.py` | `adapters/media_store.py` | 
| `_challenge_detail`, `_profile_data` helpers | `adapters/presenters.py` | 
| Grading logic previously handled on the client | Server `play/domain/` | 

## Entities

Six entities hold every business rule in the app. Today these rules are scattered across Django models, views, and the client; after the migration, each one lives in exactly one place.

| Entity | What it is | Rules it owns | Rules live today in | 
| ----- | ----- | ----- | ----- | 
| **`Challenge`** | One simulated call: name, date, difficulty, category, the right tone, the required action, the conversation tree | Must have a valid tree; answers are never shown to players | `challenges/models.py` | 
| **`ConversationNode`** | One turn in the call: customer or agent, plus its transcript and audio | Turns alternate customer $\leftrightarrow$ agent, starting with the customer; file names are safe | `validate_conversation_tree` in `challenges/models.py` | 
| **`Attempt`** | One finished play of a challenge by a user | The same submission ID can't be counted twice or reused for a different result | `save_challenge_score` in `users/views.py` | 
| **`Profile`** | A player's progress: avatar, team, best score per challenge, login days | Keep only the best score; `total` = sum of best scores; `streak` = consecutive login days | `users/models.py` + `users/views.py` | 
| **`StarRules`** | How a play is scored | 1 star each for: correct tone, answering within 10 seconds, correct action; 0–3 total | `users/views.py` (and duplicated on the client) | 
| **`AnswerMatching`** | How answers are judged | Tone is correct at cosine similarity $\ge 0.65$; action is correct when every keyword appears | `tone/views.py` (and client logic) | 

> *Note: The login account itself (username, password, session) stays with Django's built-in auth; `Profile` is the part the business cares about.*

## Use Cases

The app has **15 use cases**. The team's view that *"each endpoint is a use case"* is close but not exact: 3 endpoints are infrastructure (health, root, CSRF), 2 endpoints do the same job, 1 endpoint does two jobs, and 2 use cases are command-line only.

| Group | Use case | What the user does | Today | 
| ----- | ----- | ----- | ----- | 
| **Challenges** | `BrowseChallenges` | See and search the calendar of challenges | `GET /api/challenges/` | 
| **Challenges** | `GetChallengeForPlay` | Load a challenge, without its answers | `GET /api/challenges/<slug>/` | 
| **Play** | `GradeTone` | Get instant feedback on the tone word | `GET /api/tone/<slug>/` | 
| **Play** | `CompleteChallenge` | Submit answers, get stars, save the attempt | Score endpoint + client-side grading | 
| **Accounts** | `SignUp` | Create an account | `auth/signup/` | 
| **Accounts** | `LogIn` | Start a session | `auth/login/` | 
| **Accounts** | `LogOut` | End the session | `auth/logout/` | 
| **Accounts** | `GetCurrentUser` | Restore who is signed in | `auth/me/` | 
| **Accounts** | `ListGroups` *(icebox)* | Pick a team at signup | `groups/` | 
| **Progress** | `ViewProfile` | See scores and progress | Two endpoints, to be merged | 
| **Progress** | `UpdateProfile` | Change name, avatar, team, email | `POST /api/users/<username>/` (score fields removed) | 
| **Progress** | `ViewLeaderboard` | See top players | `leaderboard/` (no screen yet) | 
| **Progress** | `RecordDailyLogin` | Count today toward the streak | New; never called today | 
| **Content** | `ImportChallengePackage` | Add or replace a challenge | CLI + admin upload | 
| **Content** | `ValidateChallenges` | Check challenges are ready to publish | CLI only | 

The core of the product is `CompleteChallenge`; most others are simple reads or Django auth wrapped in a thin use case.

## Vertical Slices

The 15 use cases group into **6 slices**. Each slice runs from the API boundary down to the database, so one person can own it end to end.

| Slice | Use cases | Entry point | Entities used | 
| ----- | ----- | ----- | ----- | 
| **1. Finish and score** | `GetChallengeForPlay`, `CompleteChallenge` | Challenge & score endpoints | `Challenge`, `Attempt`, `Profile`, `StarRules`, `AnswerMatching` | 
| **2. Tone stage** | `GradeTone` | Tone grading endpoint | `Challenge`, `AnswerMatching` | 
| **3. Home and browse** | `BrowseChallenges`, `ViewLeaderboard` | Challenges & leaderboard endpoints | `Challenge`, `Profile` | 
| **4. Accounts** | `SignUp`, `LogIn`, `LogOut`, `GetCurrentUser`, `ListGroups` | Auth & groups endpoints | `Profile` | 
| **5. Profile and streaks** | `ViewProfile`, `UpdateProfile`, `RecordDailyLogin` | Profile & daily login endpoints | `Profile`, `Attempt` | 
| **6. Content admin** | `ImportChallengePackage`, `ValidateChallenges` | Django admin + CLI | `Challenge`, `ConversationNode` | 

Slices share entities but not files: Slice 1 writes attempts and Slice 5 only reads them, and Slice 2 builds the tone matcher that Slice 1 reuses.

## Bonus: Migration Plan

The migration is split into **two separate tracks**—**Track A (Backend)** and **Track B (Frontend)**—so API contracts are stabilized and tested before the frontend is decoupled from client-side business rules. Within each track, one person builds a shared foundation first, then teammates take slices in parallel (with Slice 1 acting as the pilot template).

### Track A: Backend Migration

#### Wave A0: Backend Foundation (1–2 days, one person)

1. Create the backend folder skeleton (`domain/`, `use_cases/`, `adapters/` across apps, plus the new `play/` app).

2. Write the six entities as plain Python classes with no Django imports.

3. Define the interfaces every slice needs (repositories, tone matcher, auth gateway, media store), without implementations.

4. Split shared backend files that would cause merge conflicts (such as `users/views.py`).

5. Add `config/container.py` to wire everything together.

*While Wave A0 runs, the rest of the team writes integration tests pinning down the current API JSON responses so refactoring cannot break existing contracts.*

#### Wave A1 & A2: Backend Slices

* **Wave A1 (Parallel Slices):** Migrate Slices 1–5 across the backend layers. Slice 1 (`Finish and score`) goes first as the pilot to establish the repository and presenter patterns.

* **Wave A2 (Follow-ups):** Complete Slice 6 (`Content admin`) and switch the score data source so `Attempt` records become the single source of truth for scores.

### Track B: Frontend Migration

Once a backend slice's API endpoints are migrated and verified, the corresponding frontend feature is refactored separately to act as a thin presentation layer.

#### Wave B0: Frontend Foundation (1 day, one person)

1. Create the feature-based folder skeleton (`features/play/`, `features/home/`, `features/accounts/`, `features/profile/`, `shared/`).

2. Split shared frontend files that cause merge conflicts (`ChallengePage.tsx`, `challenges.ts`, `App.tsx`).

3. Establish typed API client wrappers (`api.ts`) and custom state hooks (`usePlay.ts`, `useAccount.ts`) per feature.

#### Wave B1 & B2: Frontend Slices

* **Wave B1 (Parallel Feature Cleanup):** For Slices 1–5, move `fetch` calls into feature `api.ts` files, move UI state into hooks, and delete duplicated client-side rules (such as star calculation and keyword action matching) now owned by the backend.

* **Wave B2 (New Screens):** Build the missing UI views backed by the new endpoints (`/leaderboard` route, profile editing, and daily login streak triggers).

### Migration Waves: Backend & Frontend Tracks

```
flowchart LR
    subgraph Backend["Track A: Backend Migration"]
        direction TB
        A0["Wave A0 · Foundation (1–2 days)<br/>backend skeleton, 6 entities, ports,<br/>view splits, config/container.py"]
        A1["Wave A1 · Backend Slices 1–5 (parallel)<br/>Slice 1 pilot (StarRules, repos)<br/>Slices 2–5 endpoints & use cases"]
        A2["Wave A2 · Backend Follow-ups<br/>Slice 6 (Admin CLI/import)<br/>Attempts as single score source"]
        A0 --> A1 --> A2
    end

    subgraph Frontend["Track B: Frontend Migration"]
        direction TB
        B0["Wave B0 · Foundation (1 day)<br/>features/ skeleton, split App.tsx<br/>& ChallengePage.tsx, typed api.ts"]
        B1["Wave B1 · Frontend Slices 1–5 (parallel)<br/>extract hooks, strip client-side<br/>star & action grading rules"]
        B2["Wave B2 · New UI Screens<br/>/leaderboard route, profile edit,<br/>daily streak trigger"]
        B0 --> B1 --> B2
    end

    A1 -.->|API contracts ready| B1
    A1 -.->|new endpoints ready| B2


```

## Bonus: How to Migrate One Slice

Work from the inside out, separating backend and frontend PRs so every existing test stays green at each step.

### Part 1: Backend PRs (Inside-Out)

1. **Pin the behaviour.** Confirm tests cover the endpoint's current JSON responses.

2. **Rules & entities.** Move the business rules out of the view into `domain/`, with plain unit tests.

3. **Write the use case.** Create one interactor class in `use_cases/` that talks only to entities and port interfaces; test it with fake repositories.

4. **Write the adapters.** Implement ORM repositories, a presenter for the JSON payload, and a view slimmed to ~20 lines.

### Part 2: Frontend PRs (After Backend Endpoint is Live)

5. **Isolate API & state.** Move `fetch` calls into the feature's `api.ts` and component state into a custom hook.

6. **Strip business rules.** Delete any grading, star calculation, or answer-checking logic on the client so components only render server responses.

### Definition of Done

A slice is done when:

* **Backend:** Its `domain/` and `use_cases/` folders import nothing from Django, and the view holds no business logic.

* **Frontend:** Components contain no business rules and compute nothing that the server already returns.

* **Verification:** All pinned API tests, unit tests, and CI checks are green.

### Scope Cut Priority (If Time Runs Short)

Drop in this order:

1. **Frontend Wave B2:** New screens that don't exist yet (leaderboard UI, profile edit UI, streak UI)

2. **Backend Wave A2:** Slice 6 (Content admin)

3. **Backend Adapters:** Full repositories for simple read-only endpoints

**Never drop the foundations (Wave A0/B0) or Slice 1**, since Slice 1 fixes the answer leak and removes insecure client-side grading.
