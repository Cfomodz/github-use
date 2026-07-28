# Audit: Cfomodz/Inbox-Sorter

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read)

## Summary

Local Flask web app that authenticates to Gmail via OAuth2 (read-only scope),
fetches inbox metadata (From/Subject/Date) in 1,000-message batches with rate
limiting, groups emails by sender domain, caches to `cache/emails.json`, and
renders an expandable per-domain dashboard from a single vanilla-JS template.

Git history is clean — only `.env.example` placeholders were ever committed.

## Findings

### 1. Stored XSS via unescaped email-header data — critical

`templates/index.html:688-697,720`: `displayResults()` interpolates
`domain.domain` unescaped into `data-domain="..."`, inline
`onclick="toggleDomain('${domain.domain}',...)"` handlers, and the card body,
plus `email.date` at line 720 (while `sender_name`/`subject` are correctly
escaped). The domain comes from the attacker-controlled `From:` header
(`app.py:65-75`), and quotes survive extraction — e.g.
`From: x <a@evil" onmouseover=alert(1)>` breaks out of the attribute. Any
received email can execute script and read the whole cached inbox dataset.
Escape domain/date and replace inline `onclick` with dataset-based listeners.

### 2. Cache readable/mutable without auth; global, not per-session — warning

`app.py:208-254`: `/get-cached`, `/hide-domain`, `/clear-cache` never check
`'credentials' in session`, so any request to the port can dump or wipe all
cached email metadata; the cache is one shared file, so two users of the same
instance see each other's inbox. Contradicts the README's "Session-based"
security claim. Add the auth guard used by `/fetch-emails`; key cache per user.

### 3. `messageInterval` ReferenceError breaks session-expired flow — warning

`templates/index.html:628`: the 401 branch calls `clearInterval(messageInterval)`
— a variable that doesn't exist (real one is `messageTimeout`). The error is
swallowed by try/catch, so instead of the sign-in-again redirect the user gets a
confusing alert. Change to `clearTimeout(messageTimeout)`.

### 4. Refresh token in client-side cookie, hardcoded fallback SECRET_KEY — warning

`app.py:15` falls back to `'dev-secret-key-change-in-production'`; lines 175-182
put the OAuth access token, refresh token, and client secret in the Flask
session — a signed-but-not-encrypted cookie, forgeable when the default key is
live. Fail fast when `SECRET_KEY` is unset; consider server-side sessions.

### 5. Insecure OAuth transport + debug mode forced unconditionally — warning

`app.py:32-34` sets `OAUTHLIB_INSECURE_TRANSPORT=1` process-wide; line 405 runs
`debug=True` (Werkzeug debugger = RCE if the port is exposed). Gate both behind
a dev-only flag and bind `127.0.0.1`.

### 6. "Load More" inflates the total and resurrects hidden domains — warning

`app.py:380-382`: `total = cached['total'] + len(messages)` even though
`merge_domains()` (lines 101-106) drops duplicate message IDs, so "Total Emails"
drifts upward; after `/hide-domain`, the next Load More re-adds hidden domains
and re-skews the count. Compute total as the sum of merged domain counts and
persist a hidden-domains list.

### 7. OAuth callback 500s on missing state or user denial — info

`app.py:169` reads `session['state']` unguarded (KeyError → raw 500);
`flow.fetch_token()` at line 172 raises unhandled on `?error=access_denied`.
Wrap in try/except and redirect home with a friendly message.

### 8. README security claims don't match the code — info

`README.md:93-97` claims "never sent to external servers", "Session-based"
storage, and implies per-user isolation — contradicted by findings 2/4; the
loading UI's progress log (`index.html:576-590`) shows fabricated status
messages. Correct the Security section once 2 and 4 are fixed.

## TODOs

- [ ] Escape `domain.domain`/`email.date`; replace inline `onclick` interpolation with dataset listeners
- [ ] Add auth checks to `/get-cached`, `/hide-domain`, `/clear-cache`; per-user cache
- [ ] Fix `clearInterval(messageInterval)` → `clearTimeout(messageTimeout)` (index.html:628)
- [ ] Require `SECRET_KEY` at startup; move OAuth credentials out of the cookie
- [ ] Gate `OAUTHLIB_INSECURE_TRANSPORT` and `debug=True` behind dev-only flag; bind 127.0.0.1
- [ ] Recompute total from merged counts; persist hidden domains across Load More
- [ ] Handle missing state / `access_denied` in the OAuth callback
- [ ] Update README Security section to match reality
