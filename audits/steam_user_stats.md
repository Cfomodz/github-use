# Audit: Cfomodz/steam_user_stats

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read)

## Summary

Single-file Flask app that checks whether a Steam user (by 64-bit SteamID) has
played a given game "today" — really within the last 2 weeks, the finest
granularity Steam's API offers — via `IPlayerService`, with an HTML frontend
providing game-name autocomplete and playtime stats. No secrets committed: API
key comes from `STEAM_API_KEY` env var; full git history scan found no keys.

## Findings

### 1. Werkzeug debug mode exposed on all interfaces (RCE risk) — critical

`user_stats.py:179` runs `app.run(debug=True, host='0.0.0.0', port=5000)`.
`debug=True` enables the interactive debugger (arbitrary code execution on
exception; PIN bypassable) and `0.0.0.0` exposes it to every interface — and the
README tells users to run exactly this. Default to `debug=False`, bind
`127.0.0.1`, gate via env vars.

### 2. Steam API key sent over plaintext HTTP — warning

`user_stats.py:12` sets `base_url = "http://api.steampowered.com"`, transmitting
the secret `key` query param unencrypted. Steam fully supports HTTPS — switch to
`https://`.

### 3. `/check_game` returns 500/415 instead of JSON errors — warning

`user_stats.py:128-129`: `request.get_json()` raises uncaught 415/400 on bad
Content-Type or malformed JSON (HTML error page the frontend can't parse), and a
`null` body makes `data.get()` raise `AttributeError` → 500. Use
`request.get_json(silent=True) or {}`.

### 4. DOM XSS via unescaped game names in the frontend — warning

`templates/index.html:329-333` injects `game.name` from `/search_games` into
`innerHTML` (also `data-name` attrs); lines 378-381 and 414 do the same with
`data.game_name`/`data.message`. Steam catalog names are third-party strings —
a crafted app name executes script in the viewer's browser. Build nodes with
`textContent`/`createElement`.

### 5. App never initializes under a real WSGI server or `flask run` — warning

`initialize_steam_api()` (lines 157-168) is only called in the
`if __name__ == '__main__'` block, so `gunicorn user_stats:app` or `flask run`
leaves `steam_api = None` and every request returns "Steam API not configured"
even with the key set. Initialize at import time.

### 6. Outbound Steam API calls have no timeout — warning

`requests.get(url, params=params)` at lines 24 and 42 has no `timeout`; a stalled
Steam endpoint hangs the request thread indefinitely. Add `timeout=10` and
consider a shared `requests.Session`.

### 7. `search_games` crashes with KeyError on nameless library entries — warning

Line 154 indexes `game['appid']`/`game['name']` directly, but `GetOwnedGames` is
known to return entries lacking `name` for hidden/delisted apps — one such entry
500s the whole autocomplete endpoint. Use `.get()` and skip nameless entries
(lines 66-67/77-78 already do this correctly).

### 8. Repo clutter and doc gaps — info

`steam_api` is a 15 KB paste of the Valve Developer Wiki page (reproduced
MediaWiki content that shouldn't be committed); unused imports (`json`,
`datetime`, `timedelta`); dead `os.makedirs('templates', ...)` at line 177; no
LICENSE file, so the public code is all-rights-reserved. Delete the stray file
and dead code, add a license.

## TODOs

- [ ] `debug=False`, bind `127.0.0.1` by default, gate via env vars (user_stats.py:179)
- [ ] Switch `base_url` to `https://api.steampowered.com` (user_stats.py:12)
- [ ] Use `request.get_json(silent=True) or {}` in `/check_game` (user_stats.py:128)
- [ ] Escape game names — build suggestion/result DOM with `textContent` (index.html:329-333, 414)
- [ ] Call `initialize_steam_api()` at import time for WSGI/`flask run` (user_stats.py:157-171)
- [ ] Add `timeout=` to both `requests.get` calls (user_stats.py:24, 42)
- [ ] Use `.get()` and skip nameless games in `/search_games` (user_stats.py:154)
- [ ] Delete stray `steam_api` wiki dump, remove dead code, add a LICENSE
