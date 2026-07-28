# Audit: Cfomodz/StreamDrop

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read)

## Summary

Self-hosted Flask app for 24/7 unattended live streams from a cheap VPS:
renders a website/HTML file (headless Chromium) or a pygame script, captures
output (Xvfb/x11grab or headless pipelines), and pushes via FFmpeg/RTMP to
YouTube/Twitch/etc. SQLite-backed dashboard (`stream_manager.py`, the systemd
entry point) manages multiple concurrent streams with metrics, alerts, and
auto-recovery.

## Findings

### 1. Deadlock: updating or deleting a running stream hangs the whole server — critical

`stream_manager.py:2068` (`update_stream`) and `:2101` (`delete_stream`)
acquire the global non-reentrant `stream_lock` (line 28) then call
`stop_stream()` (`:2078`, `:2104`), which re-acquires it at `:2042`. Permanent
deadlock holding the lock — the monitor thread and every subsequent
start/stop/update/delete block forever. One PUT/DELETE on a live stream kills
the app. Use `threading.RLock` or an internal `_stop_stream_locked()` helper.

### 2. The "reliable" test-pattern fallback always crashes — critical

`stream_manager.py:1198`: `y={quality["resolution"].split("x")[1].rstrip()-40}`
subtracts int from str → `TypeError` before FFmpeg launches. This is the
terminal fallback for every path in `_start_smart_streaming` (`:961,976,982`),
so any headless/X11 failure ends in total start failure. Also: the "successful"
headless paths (`:1224`, `:1247`) only stream a `testsrc` placeholder (TODOs at
`:1227`, `:1250`) — real page/game capture is unimplemented on headless VPS,
the exact deployment the README advertises. Fix the int cast; implement CDP
capture or document the limitation.

### 3. Auto-recovery "full restart" can never succeed — critical

`_full_restart` (`:1845`) calls `cleanup()` then `start_streaming()`, but
`cleanup()` (`:1425`) never resets `self.status`, and `start_streaming()`
returns "Stream is already running" when status is `"live"` (`:900`). The
default strategy for `memory_exhaustion`/`critical_health`/`unknown_failure`
(`:1690-1703`) always fails — breaking the "streams restart if they fail"
promise. Set `self.status = "stopped"` first.

### 4. Display/port derived from last UUID char: crashes on hex letters, collides — critical

`:1048` does `chrome_port = 9222 + int(self.config['id'][-1])` — IDs are
`uuid4()` strings, so ~37% of streams raise `ValueError`. `:1023,1740,1763`
build `display_port = f":9{id[-1]}"` — invalid X display for hex letters and
collides whenever two streams share a last character. Use `int(id[-1], 16)` or
a proper per-stream allocator.

### 5. Many API endpoints missing authentication — critical

Unprotected: `/api/projects` GET/POST/PUT/DELETE (`:2225-2258`),
`/api/templates` all five routes (`:2261-2306`), `/api/streams/from-template`
(`:2308`), `/api/platforms` (`:2326-2365`), `/api/health/<id>` (`:2572`),
`/api/recovery/<id>` (`:2581`). `setup.sh:450` deliberately opens port 5000 to
the internet, and `GET /api/templates` returns full `template_config` blobs
that typically contain stream keys — unauthenticated secret leak plus
unauthenticated data mutation. Also `app.secret_key` falls back to per-process
random (`:2142`), logging everyone out each restart. Add `@requires_auth`
everywhere (or a blueprint-level check) and a persistent `FLASK_SECRET_KEY`.

### 6. Eight endpoints call DB methods that don't exist; multi-stream/audio updates no-op — warning

Routes call `db.get_template`/`update_template`/`delete_template`
(`:2281,2294,2303`), `create_stream_from_template` (`:2316`), four
`*_platform_config` methods (`:2331-2362`), `get_project_streams` (`:2471`) —
none exist on `StreamDatabase`; those features always return an
`AttributeError` as JSON. `db.update_stream`'s allowlist (`:310`) omits
`multi_stream_targets`/`audio_input` so the multi-targets and audio routes
never persist (audio route also uses the wrong column name; schema `:58` says
`audio_config`). And `_get_stream_targets` (`:1397`) iterates the raw JSON
string. Implement or remove; extend allowlist; fix column; `json.loads`.

### 7. `streams.db` with demo data and a stale schema committed — warning

Tracked in git despite `.gitignore:8-9` (ignore rules don't affect tracked
files). Ships fake demo streams (`test-key-123`, `custom-twitch-key`) and a
pre-`project_id` schema that `CREATE TABLE IF NOT EXISTS` never migrates —
`delete_project` (`:657`) fails with "no such column". Users who commit from
their install risk publishing real stream keys. `git rm --cached streams.db`,
create DB at first run, add a migration step.

### 8. Broken legacy tooling and unsafe defaults: `main.py` and `monitor.sh` — warning

`main.py`: `cleanup()` references `self.ffmpeg_process` never set in
`__init__` (`main.py:121`); `YOUTUBE_STREAM_KEY` checked (`:210`) but never
used, so streaming can't start; Flask `debug=True` on `0.0.0.0` (`:231`) =
remote code execution. Both `main.py:63` and `stream_manager.py:1297` pass
`--remote-debugging-address=0.0.0.0`, exposing Chrome DevTools to the network.
`monitor.sh`: typo `...wc -l)s` breaks the integer comparison (`:21`),
hardcoded `/home/toor/StreamDrop` paths, nonexistent `stream_events` table,
curls the login-protected API. Repair or delete both; bind DevTools localhost.

## TODOs

- [ ] Replace `stream_lock` with `RLock` (or lock-free internal `_stop_stream`) — fixes update/delete deadlock
- [ ] Fix `str - int` TypeError in `_start_test_pattern_streaming`; implement or document headless capture
- [ ] Reset `self.status = "stopped"` in `_full_restart` so auto-recovery works
- [ ] Derive Chrome ports / X displays collision-free (`int(uuid[-1], 16)` or allocator)
- [ ] Add `@requires_auth` to projects/templates/from-template/platforms/health/recovery routes; persistent `FLASK_SECRET_KEY`
- [ ] Implement or remove the nine missing `StreamDatabase` methods; fix allowlist + `audio_config` name; parse `multi_stream_targets`
- [ ] `git rm --cached streams.db`; create DB at first run; add schema migration
- [ ] Fix or remove `main.py` and `monitor.sh`; bind Chrome remote debugging to localhost
