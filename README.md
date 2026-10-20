# bam-_boo_! 🎋

![React](https://img.shields.io/badge/React-%2320232a.svg?logo=react&logoColor=%2361DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=fff)
![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-%2338B2AC.svg?logo=tailwind-css&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)
![Django](https://img.shields.io/badge/Django-%23092E20.svg?logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-%2307405e.svg?logo=sqlite&logoColor=white)

**bam-_boo_!** is an interactive self-training application that helps contact centre agents master the balance between speed and quality through simulated customer interactions.

At the end of each challenge, agents receive immediate feedback with a simple star-based scoring system, with stars for tone recognition, speed, and decision-making.

With **bam-_boo_!**, training turns into something agents can actually do in a couple of minutes every day. Features like daily streaks and quick challenges keep them engaged while helping them continuously refine their skills, leading to faster resolutions and improved customer satisfaction.

## Built by 🥬 team **kale**

Partnered with [**Genesys**](https://www.genesys.com/) for the [Focus in Technology Leadership](https://www.technologyleadershipinitiative.com/) as part of [CSC207H1](https://artsci.calendar.utoronto.ca/course/csc207h1) Fall 2026.

- 👍 [**K**enny Zheng](https://github.com/PyneKoyne)
- 🧋 [**A**ngela Zheng](https://github.com/angelayzheng)
- 🐼 [**A**ngelina Jiang](https://github.com/AngelsandDevsLOL)
- 🦋 [**L**aavanya Sahay](https://github.com/laavanya-sahay)
- 🎧 [**E**qraa Khan](https://github.com/Eqraa-Khan)

## Development

See [SETUP.md](docs/SETUP.md) and [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## Architecture

The React and TypeScript frontend uses Vite and Tailwind CSS. It loads challenges from Django's JSON API and guides agents through tone recognition, branching conversations, and results. During development, Vite proxies `/api/` and `/media/` requests to Django.

The Django backend stores challenges, conversation trees, user profiles, scores, and word embeddings in SQLite. Audio recordings and transcripts remain local media files served separately from the database. See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for service boundaries and [LEVELS.md](docs/LEVELS.md) for level authoring and imports.

```text
backend/
  challenges/       Challenge models, API, level imports, and source packages
  config/           Django settings and URL configuration
  counter/          Shared bam/boo count model and API
  tone/             Word embedding storage and import command
  users/            User profiles, scores, and leaderboard API
  media/            Local imported audio and transcripts (not committed)
  db.sqlite3        Local SQLite database (not committed)
  manage.py         Django command-line entry point
  requirements.txt  Python dependencies
data/
  sample-scenario.json  Legacy prototype fixture
docs/
  ARCHITECTURE.md   System design and service boundaries
  CONTRIBUTING.md   Development guidelines
  LEVELS.md         Level package format and import workflow
  SETUP.md          Local development setup
frontend/
  src/
    components/     Shared UI components and audio player
    pages/          Calendar, challenge, and results screens
    challenges.ts   Challenge API client and transcript loading
    conversation.ts Conversation traversal and answer matching
  tests/            API client and conversation tests
  package.json      npm scripts and dependencies
```
