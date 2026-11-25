# Contribution Guidelines

Read [ARCHITECTURE.md](ARCHITECTURE.md) before making structural changes. Keep it updated in the same pull request when changing services, routes, data models, frontend organization, dependencies, ports, or top-level directories.

## Backend naming

- Folders use camelCase: package folders (`useCases/`, `adapters/`, `domain/`) and use-case folders named for the use case (`manageChallengeRun/`).
- Modules use camelCase, including modules whose main contents are one class: `conversationNode.py`, `challengeValidator.py`, `unitOfWork.py`.
- Files inside a use-case folder (`useCases/<useCase>/` or `adapters/<useCase>/`) are named for their role in PascalCase: `Interactor.py`, `InputBoundary.py`, `InputData.py`, `OutputBoundary.py`, `OutputData.py`, `DataAccessInterface.py`, `Errors.py`, `Controller.py`, `Presenter.py`. The folder already names the use case, so don't repeat it in the filename.
- Tests are `test<Subject>.py` (for example `testAudio.py`) or `tests.py`. Django's test runner discovers any `test*.py` module. Shared helpers such as `testSupport.py` and `testUrls.py` match the same pattern and are imported during discovery, so keep test methods out of them.
- Management commands use snake_case (`import_challenges.py`, `seed_kale_demo.py`), because Django uses the filename as the command name. The `management/commands/` folders they live in also keep Django's required names.
- Migrations and their `migrations/` folders keep Django's generated names.
- Module paths written as strings, in `call_command(...)`, `patch(...)`, and settings such as `ROOT_URLCONF`, must match the filename exactly. Editors and type checkers don't check them.
- Rename files with `git mv`. On macOS, a rename that only changes capitalization isn't recorded otherwise. Use `git mv -f old new`, or rename through a temporary name.

## Frontend naming

- Folders and source files use camelCase: components (`profileStats.tsx`), pages (`profilePage.tsx`), the root (`app.tsx`), hooks (`useProfileFlow.ts`), and use-case folders and files (`useCases/submitTone/submitToneInteractor.ts`).
- Exported React components keep PascalCase identifiers (`export default function ProfileStats`), because JSX requires component names to start with a capital letter.

## Commit messages

Use the [Conventional Commits](https://www.conventionalcommits.org/) format:

```text
<type>[optional scope]: <description>
```

Keep the description short, specific, and written in the imperative mood. Use lowercase and do not end it with a period.

Common commit types:

- `feat`: add a user-facing feature
- `fix`: correct a bug
- `docs`: update documentation
- `refactor`: change code without changing behavior
- `test`: add or update tests
- `chore`: make maintenance changes
- `build`: change dependencies or build configuration
- `ci`: change continuous integration configuration

Examples:

```text
feat(auth): add password reset flow
fix(api): return 404 for missing projects
docs: clarify local setup
test(frontend): cover project form validation
chore: update Django dependencies
```

Prefer one logical change per commit. Keep commits small enough to review and avoid mixing formatting-only changes with behavior changes.

## Branches and pull requests

- Use the [pull request template](../.github/pull_request_template.md) when opening a PR, and include screenshots for UI changes.
- Create a branch for each change, such as `feat/project-search` or `fix/login-error`.
- Rebase or update the branch before opening a pull request when the target branch has moved.
- Include a clear summary, testing performed, and any setup or migration notes in the pull request description.
- Call out architecture changes and update [ARCHITECTURE.md](ARCHITECTURE.md) when the system structure changes.
- Keep pull requests focused and link related issues when applicable.
- Request review before merging and resolve review comments in follow-up commits (GitHub will automatically request reviews from code owners).
- `main` is protected. Do not push directly to it. Open pull requests into `main` for review and merge.

## Pre-commit checks

Enable the shared hook once per clone with `git config --local core.hooksPath .githooks`. Before every commit, `.githooks/pre-commit` runs the same frontend tests, formatting, lint, build, Django checks, Black formatting, migration checks, and backend tests as CI. A failed command blocks the commit. Checks cover the entire working tree, including unstaged changes. Install both projects' dependencies first; see [SETUP.md](SETUP.md#enable-pre-commit-checks). To run the hook manually, use `bash .githooks/pre-commit` from the repository root.

## Before opening a pull request

Run the checks relevant to your changes from the repository root:

```bash
backend/.venv/bin/python backend/manage.py check
(cd backend && .venv/bin/python manage.py test --noinput)
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
backend/.venv/bin/python -m black --check backend
cd frontend && npm test && npm run build && npm run lint && npm run lint:js
```

Also verify that new dependencies are recorded in the appropriate dependency file and that generated or local-only files are not included in the commit.

## Continuous integration

GitHub Actions runs the `Frontend` and `Backend` jobs in `.github/workflows/ci.yml` on every push and pull request. You can also start the CI workflow manually from the Actions tab after it is on the default branch. Both jobs must pass before merging; CI uses Node 24 and Python 3.14 and runs the tests and checks above.
