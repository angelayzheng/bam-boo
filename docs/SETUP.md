# Setup

## Before you start

Install Git, Node.js 24 with npm, and Python 3.14 or newer.

**On Windows, you must use WSL.** Install these tools inside WSL and use WSL Bash for setup, development, and commits. Use one Python environment at `backend/.venv`.

Run the commands below from the repository root unless noted otherwise.

### Install FFmpeg (audio normalization only)

FFmpeg is only required to run the challenge audio normalizer; it is not needed to run the app. FFmpeg is a system package, so install it separately from the Python packages in `backend/requirements.txt`.

On macOS with Homebrew:

```bash
brew install ffmpeg
```

On Debian or Ubuntu, including WSL:

```bash
sudo apt update
sudo apt install ffmpeg
```

Confirm it is available:

```bash
ffmpeg -version
```

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
backend/.venv/bin/python backend/manage.py seed_kale_demo
```

Load the ConceptNet Numberbatch word vectors (a large download, so this takes a few minutes):

```bash
backend/.venv/bin/python backend/manage.py load_vectors
```

The command downloads the vector file to `data/numberbatch-en-19.08.txt.gz` if needed. If the database contains any vectors, it skips both downloading and loading by default. Use `--clear` to replace existing vectors or `--file` to select a local compressed vector file:

```bash
backend/.venv/bin/python backend/manage.py load_vectors --clear
backend/.venv/bin/python backend/manage.py load_vectors --file /path/to/numberbatch-en-19.08.txt.gz
```

Combine `--file` with `--clear` to load a different file when vectors are already present.

The seed command imports the bundled demo challenge so the frontend has a challenge to load. Run it again with `--force` after editing the demo package.

Tailwind is included in the frontend dependencies. The virtual environment, SQLite database, and build output stay local and are not committed.

### Enable pre-commit checks

Run this once per clone:

```bash
git config --local core.hooksPath .githooks
```

The hook runs the frontend and backend CI checks before each commit. A failed check blocks the commit. Checks include unstaged changes; the hook does not stage files or fix formatting.

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

To browse it through Django admin, run:

```bash
backend/.venv/bin/python backend/manage.py createsuperuser
```

Then sign in at <http://127.0.0.1:8000/admin/> while Django is running.

For SQL access, run:

```bash
backend/.venv/bin/python backend/manage.py dbshell
```

## Troubleshooting

- **Python cannot create the environment:** install the venv package for your Python version. If uv is installed, use `uv venv --python python3 --seed backend/.venv`, then install `backend/requirements.txt` as above.
- **Switching from Windows Python:** recreate `backend/.venv` inside WSL. A Windows environment cannot be reused there.
- **Missing frontend tools:** run `cd frontend && npm ci --include=dev --bin-links=true` from WSL. This also replaces packages previously installed by Windows npm.

You can activate Python with `source backend/.venv/bin/activate`, but activation is optional when using the explicit interpreter paths above. The hook uses that interpreter by default; set `BACKEND_PYTHON` to an absolute path only if you need an override.
