# Local challenge storage

Every challenge has a unique, stable `slug`. The slug names the challenge's source folder and manifest: both are `<slug>` and `<slug>.json`. Keep the slug unchanged after publication, even if you edit the display name or schedule date. Names and slugs must also be unique under the current database model.

SQLite stores IDs, names, dates, grading metadata, and the conversation tree. Both audio and transcript contents remain local files.

## Directory layout

Author challenge packages under `backend/challenges/source_data/challenges/`, using the challenge slug as the folder name:

```text
backend/challenges/source_data/challenges/
└── forgot-password-x3/
    ├── <slug>.json
    ├── audio/                   a1.mp3 … a6.mp3, c1.mp3 … c7.mp3
    └── transcripts/             a1.txt … a6.txt, c1.txt … c7.txt
```

The importer publishes the same structure beneath `backend/media/challenges/<slug>/`. Django serves these local files through `/media/challenges/<slug>/…`. Source packages are versioned with the project; `backend/media/` and SQLite are generated local state and excluded from Git. Back up source packages, including their MP3s, before editing them.

## Add a challenge

1. Choose an unused name and slug. Create its folders, for example:

   ```bash
   slug=account-locked
   challenge_dir="backend/challenges/source_data/challenges/$slug"
   mkdir -p "$challenge_dir/audio" "$challenge_dir/transcripts"
   ```

2. Add one MP3 and one UTF-8 `.txt` transcript for every turn. Keep the same filename stem as the turn's unique `node_key`. Customer turns use `type: "question"`; agent turns use `type: "response"`.

   Every MP3 must be playable MP3 audio. The importer runs `ffprobe` on each recording and rejects the package if FFmpeg is missing, the file has no audio stream, the codec is not MP3, or the duration is invalid.

   Install FFmpeg and normalize all challenge recordings from the repository root:

   ```bash
   python3 scripts/normalize_audio.py
   ```

   The script scans challenge source packages recursively, normalizes MP3 files in place to approximately `-23 LUFS` integrated loudness and no higher than `-1.5 dBTP`, and skips files already within the target. It verifies each normalized file before replacing the original. Pass `--root <directory>` to scan a different folder. The bundled demo recordings use this target.

3. Create `<slug>.json` inside the challenge folder, for example `account-locked.json`. Here is a minimal customer–agent–customer conversation; add sibling agent nodes under a customer's `children` array to offer branching choices:

   ```json
   {
     "name": "Account Locked",
     "slug": "account-locked",
     "challenge_date": "2026-10-16",
     "difficulty": 1,
     "category": "account",
     "tone": "frustrated",
     "required_action": "unlock account",
     "conversation_tree": {
       "type": "question",
       "node_key": "c1",
       "text_file": "transcripts/c1.txt",
       "audio_file": "audio/c1.mp3",
       "children": [
         {
           "type": "response",
           "node_key": "a1",
           "text_file": "transcripts/a1.txt",
           "audio_file": "audio/a1.mp3",
           "children": [
             {
               "type": "question",
               "node_key": "c2",
               "text_file": "transcripts/c2.txt",
               "audio_file": "audio/c2.mp3",
               "children": []
             }
           ]
         }
       ]
     }
   }
   ```

4. Apply migrations and import the new challenge, or import every challenge folder:

   ```bash
   backend/.venv/bin/python backend/manage.py migrate
   backend/.venv/bin/python backend/manage.py import_challenges account-locked
   backend/.venv/bin/python backend/manage.py import_challenges
   ```

   On Windows, run these commands in WSL with the Linux environment at `backend/.venv`, as described in [SETUP.md](SETUP.md).

The importer checks that the slug matches its folder name and validates metadata, alternating turn types, unique turn keys, expected paths, nonempty files, UTF-8 transcripts, and playable MP3 audio before installing selected packages. Transcript paths and audio paths in the manifest are relative to that challenge's folder; the database stores them with the `challenges/<slug>/` prefix.

## Update an existing challenge

Edit its source package, then explicitly replace the published copy:

```bash
backend/.venv/bin/python backend/manage.py import_challenges forgot-password-x3 --replace
```

Without `--replace`, existing challenges are skipped. Replacement preserves the numeric database ID and slug, stages a complete media folder, and restores the previous published folder if saving fails. For a different challenge, create a new slug and folder instead of reusing an existing one.

## Publish through Django admin

Staff can import a challenge without shell, Git, or server access. Create a staff account, then grant only the challenge view, add, and change permissions. Do not use a superuser for routine publishing. An administrator can create the account and a `Challenge publishers` group from `/admin/`.

1. Prepare a complete package folder as described above:

   ```text
   account-locked/
     account-locked.json
     audio/
       c1.mp3
       a1.mp3
       ...
     transcripts/
       c1.txt
       a1.txt
       ...
   ```

2. Create one ZIP containing that folder as its only top-level entry. Do not upload loose files or multiple challenge folders.
3. Open `/admin/`, go to **Challenges**, and select **Import challenge package**.
4. Choose the ZIP and select **Import challenge package**. Tick **Replace an existing challenge with this slug** only when updating a challenge that already exists.
5. The package is validated before anything is changed. A successful import reports the challenge name, slug, date, and turn count. A failed import reports the exact problem and leaves the database, published media, and source package untouched.

The admin import accepts the same manifest, file layout, and validation rules as `import_challenges`. It additionally rejects path traversal, absolute paths, backslashes, symbolic links, encrypted ZIP entries, duplicate files, unsupported file types, and archives above the configured limits. macOS metadata such as `__MACOSX`, `.DS_Store`, and `._*` files are ignored. The limits are configured in `backend/config/settings.py` as `CHALLENGE_IMPORT_MAX_ARCHIVE_BYTES`, `CHALLENGE_IMPORT_MAX_UNCOMPRESSED_BYTES`, and `CHALLENGE_IMPORT_MAX_FILES`.

Admin imports publish to both `backend/media/challenges/<slug>/` and `backend/challenges/source_data/challenges/<slug>/`. The source package is the canonical copy used by validation and recovery; keep `source_data/challenges/` writable and persistent in production. Back up `backend/db.sqlite3`, `backend/media/challenges/`, and `backend/challenges/source_data/challenges/` together before importing.

The default admin add form is disabled because a valid challenge requires a complete media package. Challenge fields are read-only after import; to change metadata or content, upload an updated package and select **Replace**. This keeps the database, published media, and source package synchronized.

`seed_kale_demo` remains a shortcut for importing `forgot-password-x3`; its `--force` flag delegates to `--replace`. The bundled demo uses a fixed date and slug. Django assigns its numeric ID on first import, so IDs can differ across databases; replacement preserves the existing ID within a database. Use the slug to identify the same challenge across machines.

## Validate production challenge data

Run the validation command before deployments and after imports, when no import is in progress:

```bash
backend/.venv/bin/python backend/manage.py validate_challenges
```

The command is read-only. It prints `OK` and exits `0` only when the database, published media, and source packages are production-ready. Otherwise it prints one `ERROR: ...` line per breaking issue and exits non-zero. It has no warnings, no informational summaries, and no optional modes.

It checks:

- Database integrity and applied migrations.
- Challenge rows pass model validation and have a nonempty conversation tree.
- Every tree node has the exact expected transcript and audio path.
- Every referenced published file exists, is a regular nonempty readable file under `MEDIA_ROOT`, and resolves to the URL generated by the API.
- Transcripts are valid UTF-8 and nonblank.
- `MEDIA_ROOT` and `source_data/challenges/` exist and `MEDIA_URL` is configured.
- Every challenge has a source package whose metadata and tree match the database.
- Every source file is byte-identical to its published media copy.

Existing challenges imported before source persistence must be re-imported, or have their published folders copied into `source_data/challenges/`, before validation can pass.

It intentionally does not check duplicate dates, schedule coverage, orphan media, unreferenced files, tree size, admin log entries, or non-challenge models.

The challenge list and detail APIs expose both `id` (the existing numeric database key) and `slug` (the stable package identifier). The current frontend still selects the working demo by slug; this storage layout and import command support adding further challenges independently of a future challenge-selection UI.
