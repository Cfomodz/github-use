# Audit: Cfomodz/Brother-QL-710W_Incrementing-Label-Creator

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read)

## Summary

Flask web service that drives a Brother QL-710W label printer over Wi-Fi (via
`brother_ql`): each POST to `/print` increments a persistent per-category counter
(`counters.json`) and prints a label with category name, auto-incremented item
number, date, and a Code128 barcode — built for Whatnot live sellers tapping a
Stream Deck key per sold item. `service_server.py` exposes an endpoint to launch
the print server; `index.html` is a minimal browser UI.

## Findings

### 1. App crashes on startup: imports of template modules that don't exist — critical

`whatsnot_live_label_writer.py:12-13` (sic: `whatnot_live_label_writer.py`) imports
`templates.logo_template` and `templates.coupon_template`, but the tracked
`templates/` package contains only `__init__.py` — the modules are absent from all
git history. A fresh clone dies with `ModuleNotFoundError` before Flask starts, so
nothing in the repo is runnable. Commit the missing modules or delete the imports
and the `logo`/`coupon` branches in `print_label()` (lines 157-161).

### 2. No requirements.txt / dependency manifest at all — critical

Code imports `flask`, `flask_cors`, `brother_ql`, `PIL`, `barcode`, `dotenv` but
there is no manifest or setup docs. `brother_ql` is unmaintained and breaks with
Pillow >= 10 (removed `Image.ANTIALIAS`), so even a reverse-engineered install
fails. Add `requirements.txt` pinning `brother_ql` + `Pillow<10` (or switch to
`brother_ql_next`).

### 3. Barcode "type code" is non-deterministic across restarts — warning

`whatnot_live_label_writer.py:60` uses `hash(label_type) % 100`; Python string
hashing is salted per process, so the same label type encodes differently after
every restart — anything keyed on that code silently breaks. Use a stable digest,
e.g. `zlib.crc32(label_type.encode()) % 100`.

### 4. Unauthenticated endpoints on 0.0.0.0 with open CORS — warning

Both servers bind `0.0.0.0` (`whatnot_live_label_writer.py:467`,
`service_server.py:30`) with `CORS(app)` wide open and no auth: anyone on the LAN
(or any web page the operator visits) can burn label stock via `/print`, wipe
state via `/clear_counters`, or stack duplicate server processes via
`/start-service` (no idempotency guard). Bind localhost or add a shared-secret
header, restrict CORS, track the spawned process.

### 5. Counter race condition can print duplicate label numbers — warning

`/print` (lines 255-258) and `/print_custom` (lines 305-308) do unlocked
read-increment-write on the shared counters dict + full-file rewrite; Flask's
threaded dev server means two rapid taps can print the same number — the exact
failure this tool exists to prevent. Guard with `threading.Lock`.

### 6. Custom-text rendering: wrong height math, crash on blank lines — warning

`print_label()` computes `image_height` from raw `\n` count (lines 121-123) but
draws with `draw_wrapped_text()` which may wrap one line into several — overflow
and cut-off text; a blank line crashes with `IndexError` at `words[0]` (line 67).
Measure wrapped height first (as `/print_custom` does) and guard empty strings.

### 7. index.html hardcodes localhost, defeating the network setup — info

`index.html:21` fetches `http://localhost:5000/print` even though the server
binds `0.0.0.0` for remote use — from any other device prints silently fail. Use
a relative `fetch('/print', ...)` (the same Flask app serves the page), which
also removes the need for CORS.

### 8. No setup docs; machine-specific hardcoding; stale repo references — info

README has zero install/run docs; `PRINTER_IP = '10.0.0.13'` is hardcoded
(line 23) along with Windows-only `arial.ttf`/`arialbd.ttf` fonts (silently falls
back to Pillow's tiny bitmap font on Linux/macOS); README title/badge reference a
different repo name (`Whatnot-Item-Label-Creator`); `counters.json` is committed
with live data despite `*.json` in `.gitignore`. Move config to `.env`, document
setup, `git rm --cached counters.json`.

## TODOs

- [ ] Commit `templates/logo_template.py` + `templates/coupon_template.py`, or remove dead imports/branches
- [ ] Add `requirements.txt` with pinned `brother_ql` and `Pillow<10` (or a maintained fork)
- [ ] Replace `hash(label_type) % 100` with a stable digest (`zlib.crc32`)
- [ ] Add auth/origin restrictions, sensible binding, idempotent `/start-service`
- [ ] Wrap counter increment + save in a `threading.Lock`
- [ ] Fix custom-text height calculation; guard `draw_wrapped_text` against empty lines
- [ ] Change `index.html` to a relative `/print` URL
- [ ] Document setup in README, move printer IP/fonts to `.env`, untrack `counters.json`, fix stale badge/repo name
