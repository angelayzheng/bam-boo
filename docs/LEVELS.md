# Local level storage

Every level has a stable, unique `level_id` and a separate display `name`. Use `YYYY-MM-DD-slug` for the ID, for example `2026-10-15-forgot-password-x3`. The slug distinguishes multiple levels on the same date. Keep the ID and folder name unchanged after publication, even if you edit the display name or schedule date. Names and slugs must also be unique under the current database model.

SQLite stores IDs, names, dates, grading metadata, and the conversation tree. Both audio and transcript contents remain local files.

## Directory layout

Author level packages under `backend/challenges/source_data/levels/`. The working recording has been moved into this layout:

```text
backend/challenges/source_data/levels/
└── 2026-10-15-forgot-password-x3/
    ├── level.json
    ├── audio/
    │   ├── customer/            c1.mp3 … c7.mp3
    │   └── agent/               a1.mp3 … a6.mp3
    └── transcripts/
        ├── customer/            c1.txt … c7.txt
        └── agent/               a1.txt … a6.txt
```

The importer publishes the same structure beneath `backend/media/levels/<level_id>/`. Django serves these local files through `/media/levels/<level_id>/…`. Source packages are versioned with the project; `backend/media/` and SQLite are generated local state and excluded from Git. Back up source packages, including their MP3s, before editing them.

## Add a level

1. Choose an unused ID, name, and slug. Create its folders, for example:

   ```bash
   level_id=2026-10-16-account-locked
   level_dir="backend/challenges/source_data/levels/$level_id"
   mkdir -p "$level_dir/audio/customer" "$level_dir/audio/agent"
   mkdir -p "$level_dir/transcripts/customer" "$level_dir/transcripts/agent"
   ```

2. Add one MP3 and one UTF-8 `.txt` transcript for every turn. Keep the same filename stem as the turn's unique `node_key`. Customer turns use `type: "question"`; agent turns use `type: "response"`.

3. Create `level.json` inside the level folder. Here is a minimal customer–agent–customer conversation; add sibling agent nodes under a customer's `children` array to offer branching choices:

   ```json
   {
     "level_id": "2026-10-16-account-locked",
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
       "text_file": "transcripts/customer/c1.txt",
       "audio_file": "audio/customer/c1.mp3",
       "children": [
         {
           "type": "response",
           "node_key": "a1",
           "text_file": "transcripts/agent/a1.txt",
           "audio_file": "audio/agent/a1.mp3",
           "children": [
             {
               "type": "question",
               "node_key": "c2",
               "text_file": "transcripts/customer/c2.txt",
               "audio_file": "audio/customer/c2.mp3",
               "children": []
             }
           ]
         }
       ]
     }
   }
   ```

4. Apply migrations and import the new level, or import every level folder:

   ```bash
   backend/.venv/bin/python backend/manage.py migrate
   backend/.venv/bin/python backend/manage.py import_levels 2026-10-16-account-locked
   backend/.venv/bin/python backend/manage.py import_levels
   ```

   On Windows, use `backend/.venv/Scripts/python.exe` in place of `backend/.venv/bin/python`.

The importer checks IDs, metadata, alternating turn types, unique turn keys, expected paths, nonempty files, and UTF-8 transcripts before installing selected packages. Transcript paths and audio paths in the manifest are relative to that level's folder; the database stores them with the `levels/<level_id>/` prefix.

## Update an existing level

Edit its source package, then explicitly replace the published copy:

```bash
backend/.venv/bin/python backend/manage.py import_levels 2026-10-15-forgot-password-x3 --replace
```

Without `--replace`, existing levels are skipped. Replacement preserves the numeric database ID and `level_id`, stages a complete media folder, and restores the previous published folder if saving fails. For a different level, create a new ID and folder instead of reusing an existing slug.

`seed_kale_demo` remains a shortcut for importing `2026-10-15-forgot-password-x3`; its `--force` flag delegates to `--replace`. The bundled demo uses a fixed date and ID, so its identity is consistent across machines and repeated imports.

The challenge list and detail APIs expose both `id` (the existing numeric database key) and `level_id` (the stable package ID). The current frontend still selects the working demo; this storage layout and import command support adding further levels independently of a future level-selection UI.
