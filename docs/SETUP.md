# Setup

## Prerequisites

Install the following before setting up the repository:

- Git
- Node.js and npm
- Python 3.14 or newer

Verify the installations:

**Linux / macOS:**
```bash
git --version
node --version
npm --version
python3 --version
```

**Windows (CMD / PowerShell):**
```cmd
git --version
node --version
npm --version
python --version
```

---

## First-time setup

Clone the repository and open its root directory:

```bash
git clone <repository-url>
cd bam-boo
```

### Frontend

Install the frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

The frontend uses Tailwind CSS through the Vite plugin. Tailwind is installed with the frontend dependencies, so no separate CSS setup command is required after `npm install`.

### Backend

Create the local Python virtual environment, install dependencies, and run initial migrations:

**Linux / macOS:**
```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python backend/manage.py migrate
```

**Windows (CMD / PowerShell):**
```cmd
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe backend\manage.py migrate
```

*(Note: On Windows PowerShell/CMD, you can also activate the virtual environment with `backend\.venv\Scripts\activate` to simplify command execution).*

The virtual environment and SQLite database are local development files and are excluded from Git.

### Load the working recording

After migrations, import every local level package (currently the “Forgot Password x3” recording):

```bash
backend/.venv/bin/python backend/manage.py import_levels
```

On Windows, use `backend/.venv/Scripts/python.exe` in place of `backend/.venv/bin/python`. Packages live under `backend/challenges/source_data/levels/<level_id>/`; each has a `level.json`, MP3 audio, and UTF-8 text transcripts. The importer saves metadata and the conversation tree in SQLite and publishes the local files under `backend/media/levels/<level_id>/`.

Existing levels are skipped. To update their files and metadata while keeping their database IDs, run `import_levels --replace`. The existing `seed_kale_demo` command still imports just the demo, and `seed_kale_demo --force` replaces it. See [LEVELS.md](LEVELS.md) for the folder layout, manifest format, and adding levels.

Run both development servers below. The frontend loads the recording through Django’s `/api/challenges/` endpoints and plays recorded MP3s through `/media/`. Vite proxies both paths to port 8000. Choose an agent reply, hear the matching customer response, and continue along that branch before submitting a next action. Browser autoplay may require pressing Play first.

If the frontend shows “No recordings are available,” run `import_levels`. If transcripts or audio are missing, run `import_levels --replace`. A backend connection error requires starting Django on port 8000.

---

## Running locally

Run the backend from the repository root in the first terminal:

**Linux / macOS:**
```bash
backend/.venv/bin/python backend/manage.py runserver
```

**Windows (CMD / PowerShell):**
```cmd
backend\.venv\Scripts\python.exe backend\manage.py runserver
```

The backend runs at <http://127.0.0.1:8000>. Its health endpoint is <http://127.0.0.1:8000/api/health/>.

### View persisted data

The SQLite database is stored at `backend/db.sqlite3`. To view the saved counter in a browser, create a local Django admin account:

**Linux / macOS:**
```bash
backend/.venv/bin/python backend/manage.py createsuperuser
```

**Windows (CMD / PowerShell):**
```cmd
backend\.venv\Scripts\python.exe backend\manage.py createsuperuser
```

With the backend running, open <http://127.0.0.1:8000/admin/> and sign in. The `Counter` entry shows the current value and last update time.

For direct SQLite inspection, run:

**Linux / macOS:**
```bash
backend/.venv/bin/python backend/manage.py dbshell
```

**Windows (CMD / PowerShell):**
```cmd
backend\.venv\Scripts\python.exe backend\manage.py dbshell
```

Then query the counter:

```sql
SELECT key, value, updated_at FROM counter_counter;
```

Run the frontend from the repository root in a second terminal:

```bash
cd frontend
npm run dev
```

The frontend runs at <http://localhost:5173>.

## Recommended VS Code extensions

The workspace recommends these extensions in `.vscode/extensions.json`:

- **Prettier - Code formatter** (`esbenp.prettier-vscode`) for TypeScript, TSX, JavaScript, JSON, CSS, and Markdown.
- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`) for Tailwind class completion and diagnostics.
- **Black Formatter** (`ms-python.black-formatter`) for Python formatting.
- **Python** (`ms-python.python`) for Python language support and virtual-environment selection.

Format-on-save is enabled in `.vscode/settings.json`. Prettier also uses `prettier-plugin-tailwindcss` to sort Tailwind classes consistently.

---

## Validation

Run Django’s checks:

**Linux / macOS:**
```bash
backend/.venv/bin/python backend/manage.py check
```

**Windows (CMD / PowerShell):**
```cmd
backend\.venv\Scripts\python.exe backend\manage.py check
```

Check Python formatting with Black:

**Linux / macOS:**
```bash
backend/.venv/bin/python -m black --check backend
```

**Windows (CMD / PowerShell):**
```cmd
backend\.venv\Scripts\python.exe -m black --check backend
```

Build the frontend for production:

```bash
cd frontend
npm run build
```

Run frontend behavior tests with Node 22.18+ or 24+:

```bash
cd frontend
npm test
```

Check frontend formatting with Prettier and TypeScript/JavaScript quality with Oxlint:

```bash
cd frontend
npm run lint
npm run lint:js
```

Use `npm run format` to apply Prettier formatting locally.

When adding frontend UI, use Tailwind utility classes in React components. Keep the Tailwind import in `frontend/src/index.css` and update `frontend/vite.config.ts` if the styling build integration changes.
