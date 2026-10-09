# Contribution Guidelines

Read [ARCHITECTURE.md](ARCHITECTURE.md) before making structural changes. Keep it updated in the same pull request when changing services, routes, data models, frontend organization, dependencies, ports, or top-level directories.

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

For breaking changes, add `!` after the type or scope and explain the change in the commit body or footer:

```text
feat(api)!: replace project response format
```

Prefer one logical change per commit. Keep commits small enough to review and avoid mixing formatting-only changes with behavior changes.

## Branches and pull requests

- Use the [pull request template](../.github/pull_request_template.md) when opening a PR, and include screenshots for UI changes.
- Create a branch for each change, such as `feat/project-search` or `fix/login-error`.
- Rebase or update the branch before opening a pull request when the target branch has moved.
- Include a clear summary, testing performed, and any setup or migration notes in the pull request description.
- Call out architecture changes and update [ARCHITECTURE.md](ARCHITECTURE.md) when the system structure changes.
- Keep pull requests focused and link related issues when applicable.
- Request review before merging and resolve review comments in follow-up commits.

## Before opening a pull request

Run the checks relevant to your changes from the repository root:

```bash
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python -m black --check backend
cd frontend && npm run build && npm run lint && npm run lint:js
```

Also verify that new dependencies are recorded in the appropriate dependency file and that generated or local-only files are not included in the commit.
