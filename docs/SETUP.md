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

### WSL setup

WSL needs Linux runtimes. If `backend/.venv` already contains a Windows environment, keep it and create a separate ignored environment from Bash:

```bash
python3 -m venv backend/.venv-wsl
backend/.venv-wsl/bin/python -m pip install -r backend/requirements.txt
```

Install Node.js 24 inside WSL and run `cd frontend && npm ci` there to install native dependencies. The hook uses Node on PATH; if Node or npm cannot run, it loads an existing nvm installation from `$NVM_DIR` or `$HOME/.nvm` and selects Node 24. It does not install runtimes or dependencies during commits.

### Enable pre-commit checks

After installing frontend and backend dependencies, run this once per clone from the repository root:

```bash
git config --local core.hooksPath .githooks
```

Git runs the frontend and backend CI checks before each commit and blocks the commit if any check fails. The hook requires Bash, Node.js 24 with npm on your PATH, frontend dependencies, and the backend virtual environment. It detects both `backend/.venv/bin/python` and `backend/.venv/Scripts/python.exe`.

Run all checks manually with `bash .githooks/pre-commit`. The hook checks the entire working tree, including unstaged changes, and does not stage files or apply formatting fixes. Each run includes the frontend build and both test suites.

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

Run backend tests with Django’s test runner (it creates and migrates an isolated test database):

```bash
backend/.venv/bin/python backend/manage.py test --noinput
```

On Windows, use `backend/.venv/Scripts/python.exe` in place of `backend/.venv/bin/python`.


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

Check frontend formatting with Prettier and TypeScript/JavaScript quality with Oxlint:

```bash
cd frontend
npm run lint
npm run lint:js
```

Use `npm run format` to apply Prettier formatting locally.

When adding frontend UI, use Tailwind utility classes in React components. Keep the Tailwind import in `frontend/src/index.css` and update `frontend/vite.config.ts` if the styling build integration changes.

Run frontend route tests with `cd frontend && npm test`. They use Node 24’s built-in test runner and native TypeScript/JSON imports, without starting Vite.

The hook prefers `backend/.venv/Scripts/python.exe` under Git Bash on Windows. On Linux/WSL it selects `backend/.venv/bin/python`, then `backend/.venv-wsl/bin/python`. Set `BACKEND_PYTHON` to an absolute interpreter path to override this selection.

Windows and WSL need different native npm packages. After switching environments in a shared checkout, run `npm ci` in `frontend` from the environment where you will commit or build. Activating a Python virtual environment does not switch the Node/npm platform.

If PowerShell reports that `prettier` is not recognized, reinstall the frontend development dependencies and Windows command shims from PowerShell:

```powershell
cd frontend
npm ci --include=dev --bin-links=true
npm run lint
cd ..
```

A WSL-installed `node_modules` contains Unix links instead of the `.cmd` launchers used by Windows npm. The hook checks the local tool launchers before running checks and reports how to repair them.
