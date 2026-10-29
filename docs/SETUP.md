# Setup

## Before you start

Install Git, Node.js 24 with npm, and Python 3.14 or newer.

**On Windows, you must use WSL.** Install these tools inside WSL and use WSL Bash for setup, development, and commits. Use one Python environment at `backend/.venv`.

Run the commands below from the repository root unless noted otherwise.

## First-time setup

Clone the repository and enter its folder:

```bash
git clone <repository-url>
cd bam-boo
```

Install frontend dependencies:

```bash
cd frontend
npm ci
cd ..
```

Create the backend environment, install dependencies, and prepare the database:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py seed_local_superuser
backend/.venv/bin/python backend/manage.py seed_kale_demo
```

Load the ConceptNet Numberbatch word vectors (a large download, so this takes a few minutes):

```bash
backend/.venv/bin/python backend/manage.py load_vectors
```

The command downloads the vector file if needed. If vectors are already present, it skips loading by default. 

`seed_local_superuser` creates the same development account in each clone's local database:

- **Username:** `admin`
- **Password:** `teamkale`
- **Email:** `admin@example.test`

Use these credentials on the frontend login page or at <http://127.0.0.1:8000/admin/>. The account and its profile are created together. Rerunning the command preserves an existing active superuser's password, email, and progress. If `admin` is already used by a regular or inactive account, the command stops without changing it; rename that account before rerunning. These shared credentials are for local development only, and the command requires `DEBUG=True`.

`seed_kale_demo` imports the bundled demo challenge so the frontend has a challenge to load. Run it again with `--force` after editing the demo package.

Tailwind is included in the frontend dependencies. The virtual environment, SQLite database, and build output stay local and are not committed.

### Enable pre-commit checks

Run this once per clone:

```bash
git config --local core.hooksPath .githooks
```

The hook runs the frontend and backend CI checks before each commit. A failed check blocks the commit. Checks include unstaged changes; the hook does not stage files or fix formatting.

## Updating an existing clone

After pulling model changes, apply migrations before restarting Django:

```bash
backend/.venv/bin/python backend/manage.py migrate
```

The challenge-attempt migration keeps existing best scores and adds storage for every future completion, including its original completion time and server receipt time. View full history under **Users → Challenge attempts** in Django admin; the frontend profile shows best scores only.

## Run the app

Start Django in one terminal:

```bash
backend/.venv/bin/python backend/manage.py runserver
```

Start Vite in another:

```bash
cd frontend
npm run dev
```

Open the app at <http://localhost:5173>. Django runs at <http://127.0.0.1:8000>; check <http://127.0.0.1:8000/api/health/> if the backend seems unavailable.

## Check your changes

Run the same checks as CI:

```bash
bash .githooks/pre-commit
```

This runs both test suites, Django configuration and migration checks, Black and Prettier formatting checks, frontend lint, and the production build.

To fix formatting:

```bash
backend/.venv/bin/python -m black backend
cd frontend
npm run format
```

## Editor and database tools

For VS Code on Windows, open the project from WSL with `code .`. Select `backend/.venv/bin/python` as the Python interpreter and install the workspace's recommended extensions. Format-on-save is already configured.

The local database is `backend/db.sqlite3`.

To browse it through Django admin, sign in at <http://127.0.0.1:8000/admin/> with the default development account created during setup. To create a separate personal superuser, run:

```bash
backend/.venv/bin/python backend/manage.py createsuperuser
```

Keep Django running while using the admin site.

For SQL access, run:

```bash
backend/.venv/bin/python backend/manage.py dbshell
```

## Troubleshooting

- **Changes are not appearing in the browser:** restart Vite (`cd frontend && npm run dev`) and refresh the page. File watching uses polling so changes in mounted Windows workspaces are detected. Restart Django after backend changes if its running process still serves old code.

- **Python cannot create the environment:** install the venv package for your Python version. If uv is installed, use `uv venv --python python3 --seed backend/.venv`, then install `backend/requirements.txt` as above.
- **Switching from Windows Python:** recreate `backend/.venv` inside WSL. A Windows environment cannot be reused there.
- **Missing frontend tools:** run `cd frontend && npm ci --include=dev --bin-links=true` from WSL. This also replaces packages previously installed by Windows npm.

You can activate Python with `source backend/.venv/bin/activate`, but activation is optional when using the explicit interpreter paths above. The hook uses that interpreter by default; set `BACKEND_PYTHON` to an absolute path only if you need an override.
