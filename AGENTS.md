# Repository Agent Guidance

## Project overview

This repository contains a full-stack application:

- `frontend/`: React application built with Vite and npm.
- `backend/`: Django project using SQLite for local development.
- `docs/`: Setup and contribution documentation.

Read `docs/SETUP.md` for local installation, `docs/CONTRIBUTING.md` for contribution workflow and commit conventions, and `docs/ARCHITECTURE.md` for system boundaries and ownership.

## Working conventions

- Keep changes focused on the requested behavior.
- Follow the existing structure and avoid introducing new frameworks or abstractions without a clear need.
- Use Bash commands and forward-slash paths in documentation.
- Keep frontend dependencies in `frontend/package.json`.
- Keep backend dependencies in `backend/requirements.txt`.
- Use Tailwind CSS utility classes for frontend component styling; keep the Tailwind import in `frontend/src/index.css`.
- Do not commit virtual environments, SQLite databases, dependency directories, or build output.
- Update relevant documentation when setup or developer workflow changes.
- Update `docs/ARCHITECTURE.md` in the same change when a service, route boundary, data model, directory, dependency, or other structural decision changes.

## Validation

Run the checks relevant to the files changed. From the repository root:

```bash
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python -m black --check backend
cd frontend && npm run build && npm run lint && npm run lint:js
```

For backend changes, also run migrations when models change:

```bash
backend/.venv/bin/python backend/manage.py makemigrations
backend/.venv/bin/python backend/manage.py migrate
```

For frontend changes, run the formatter and JavaScript lint commands:

```bash
cd frontend && npm run lint && npm run lint:js
```

Do not claim a check passed unless it was actually run. Report any unavailable or failing checks clearly.

## Commit and pull request guidance

Use Conventional Commits:

```text
<type>[optional scope]: <description>
```

Use focused commits and branches. Pull requests should explain the change, list validation performed, and call out migrations, dependency changes, or other setup requirements.

## Editing guidance

- Preserve unrelated user changes.
- Prefer small, reviewable edits.
- Avoid committing secrets or local environment files.
- Add tests for new behavior when a suitable test location exists.
