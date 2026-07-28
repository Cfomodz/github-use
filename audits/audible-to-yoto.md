# Audit: Cfomodz/audible-to-yoto

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read)

## Summary

Personal-use pipeline that downloads an Audible library via `audible-cli`,
decrypts AAX with activation bytes, and uses ffmpeg to split books into
per-chapter MP3s for the Yoto kids' audio player. Companion Python scripts
generate 400x400 cover art, 16x16 chapter icons, and Yoto-format playlist JSON
plus upload instructions.

## Findings

### 1. ffmpeg invocation broken three ways in the conversion loop — critical

`convert_audiobooks.sh:217-220, 273-280`: (a) `-y -loglevel error -stats` placed
*after* the output filename, so ffmpeg ignores them; (b) ffmpeg runs inside a
`while read` loop (line 302) without `-nostdin`, so it swallows the remaining
stdin file list — after the first book, remaining books are silently skipped;
(c) line 280's `if` tests grep's exit status (`2>&1 | grep -v "^size="`), not
ffmpeg's — success/failure reporting is inverted in both directions. Add
`-nostdin`, move flags before the output path, test ffmpeg's status directly.

### 2. `set -e` makes the script's own error handling dead code — warning

`convert_audiobooks.sh:7` sets `set -e`, but failing command substitutions the
script intends to handle kill it instead: `ACTIVATION_BYTES=$(audible
activation-bytes ...)` (line 47; friendly error at 49-53 unreachable) and
`chapter_json=$(ffprobe ...)` (lines 203-204; one corrupt AAX aborts the whole
batch instead of hitting the `FAILED` path). Append `|| true` to those
substitutions. Also: line 55 echoes the activation bytes (a decryption secret)
to the terminal unnecessarily.

### 3. README badges point at CI that doesn't exist, with placeholder username — warning

`README.md:3-5` shows Tests/Lint/Documentation badges for
`github.com/YOUR_USERNAME/...` — `.github/` contains only `FUNDING.yml`, and
`YOUR_USERNAME` was never replaced (also `CONTRIBUTING.md:53`). `setup.sh:98`
points to a nonexistent `docs/README.md`. Fix the badges (or add the workflows —
a pytest run would be trivial since tests exist) and the doc pointer.

### 4. requirements.txt doesn't match reality — warning

pytest is commented out (`requirements.txt:11`) even though a full `tests/`
suite ships and `CONTRIBUTING.md:61` says this is the dev setup; `tqdm` is
required but never imported; `setup.sh:32-37` + `README.md:82-84` demand
ImageMagick and curl which nothing uses. Add pytest (dev requirements), drop
tqdm, remove the phantom dependency checks.

### 5. Playlist URL options wired wrong — warning

`generate_playlists.py:71,102` gate both cover and audio URLs on
`audio_base_url != DEFAULT_AUDIO_URL`, and line 247 sets `use_placeholders` from
`--audio-url` only — so `--cover-url` alone is silently ignored, and interactive
option 1 still emits `TODO:` strings. The `use_placeholders` flag also means the
opposite of its name. Gate cover URLs on `cover_base_url`, treat either custom
URL as intent, rename/invert the flag.

### 6. Inconsistent filename sanitization breaks cover lookups — warning

`generate_covers.py:401` saves covers as `sanitize_filename(book_name).jpg`, but
its own pre-count (line 377), `generate_chapter_icons.py:232`, and
`generate_playlists.py:135` all look up the *unsanitized* name. Any title with
`< > : " / \ | ? *` (colons are common) gets a cover the other scripts can never
find. Extract one shared `sanitize_filename()` and use it everywhere.

### 7. Documented Yoto API endpoints appear wrong — info

`generate_playlists.py:143` and `docs/YOTO_*.md` point at `api.yoto.io/v1/icons`
and `yoto.io/myo`; Yoto's published developer API lives at `api.yotoplay.com`
(OAuth via `login.yotoplay.com`) and MYO cards at `my.yotoplay.com`, with no
public "upload playlist JSON" flow. Verify against yoto.dev and update.

### 8. Chapterless books silently dropped by icon/playlist generators — info

`convert_audiobooks.sh:216-219` produces `Full Book.mp3` for chapterless AAX,
but `generate_chapter_icons.py:225-229` and `generate_playlists.py:322-326` only
glob `Chapter_*.mp3` and skip those books with no hint why. Treat `Full
Book.mp3` as a one-chapter book.

## TODOs

- [ ] Fix ffmpeg calls: `-nostdin`, flags before output path, stop deriving success from grep
- [ ] Guard command substitutions with `|| true` so `set -e` doesn't bypass error handling; stop echoing activation bytes
- [ ] Replace `YOUR_USERNAME` badges, add the referenced workflows (or delete badges), fix setup.sh doc pointer
- [ ] Add pytest to dev requirements, remove unused tqdm, drop ImageMagick/curl checks
- [ ] Rework URL handling so `--cover-url` works independently; fix interactive option 1; rename inverted flag
- [ ] Centralize `sanitize_filename()` across all cover read/write sites
- [ ] Verify and correct Yoto endpoints in generate_playlists.py and docs
- [ ] Handle chapterless books (`Full Book.mp3`) in icon and playlist generators
