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

The importer checks that the slug matches its folder name and validates metadata, alternating turn types, unique turn keys, expected paths, nonempty files, and UTF-8 transcripts before installing selected packages. Transcript paths and audio paths in the manifest are relative to that challenge's folder; the database stores them with the `challenges/<slug>/` prefix.

## Update an existing challenge

Edit its source package, then explicitly replace the published copy:

```bash
backend/.venv/bin/python backend/manage.py import_challenges forgot-password-x3 --replace
```

Without `--replace`, existing challenges are skipped. Replacement preserves the numeric database ID and slug, stages a complete media folder, and restores the previous published folder if saving fails. For a different challenge, create a new slug and folder instead of reusing an existing one.

`seed_kale_demo` remains a shortcut for importing `forgot-password-x3`; its `--force` flag delegates to `--replace`. The bundled demo uses a fixed date and slug. Django assigns its numeric ID on first import, so IDs can differ across databases; replacement preserves the existing ID within a database. Use the slug to identify the same challenge across machines.

The challenge list and detail APIs expose both `id` (the existing numeric database key) and `slug` (the stable package identifier). The current frontend still selects the working demo by slug; this storage layout and import command support adding further challenges independently of a future challenge-selection UI.
