# Audit: Cfomodz/spam-baiter

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read)

## Summary

Scam-baiting toolkit: `voice_search_baiter.py` plays pre-recorded "Walter
Nelson" soundboard WAVs over a phone line via PyAudio, following a scripted
GMB/SEO-scam call flow with silence detection and tiered fillers; a newer
FastAPI + React/Vite dashboard (`backend/`, `frontend/`) adds multi-line mock
call control, ElevenLabs TTS clip generation, a soundboard UI, and contact
management.

No committed secrets — single squashed commit, `.env` gitignored, only a
placeholder `.env.example`.

## Findings

### 1. Filler rotation references audio files that don't exist — crashes mid-call — critical

`voice_search_baiter.py:14-15` lists `"Sure thing.wav"` (on disk: `Sure
Thing.wav`, case matters on Linux) and `"I understand.wav"` (doesn't exist at
all in `tier_1/`). `respond_to_scammer()` (line 185) does a bare `open()`, so
the 4th and 8th tier-1 filler in the round-robin raises `FileNotFoundError` and
kills the script during a live call. Fix the names, add/drop the missing
recording, and skip missing files gracefully.

### 2. `PHONE_BRIDGE=bluetooth` imports a module that doesn't exist — critical

`backend/app/services/line_manager.py:15` imports `.bluetooth_bridge`, which is
nowhere in the repo, while `backend/app/config.py:20` advertises `"bluetooth"`
as a valid `Literal` value and `.env.example` documents it. Setting it crashes
startup with `ModuleNotFoundError`. Commit the bridge or remove the option with
a clear config error.

### 3. Root requirements.txt can't install on the advertised Python — critical

Pins `pyaudio==0.2.11` and `numpy==1.21.2`, but the README badge says Python
3.12; numpy 1.21.2 supports ≤3.10 and pyaudio needs 0.2.12+ for 3.11+. README
step 2 fails outright. Bump to `pyaudio>=0.2.14` and modern numpy (match
`backend/requirements.txt`).

### 4. Every TTS generation adds a duplicate, unplayable clip card — warning

`backend/app/routers/tts.py:34-44` broadcasts `clip_ready` to all WS clients
including the originator; `frontend/src/hooks/useWebSocket.ts:31-40` adds it
with `file_path: ""` while `TTSPanel.tsx:27-28` also adds the full clip from the
HTTP response — two cards, one of which plays `new Audio("/audio/")` and
silently fails (`ClipCard.tsx:20`). Include `file_path` in the WS payload and
dedupe by id.

### 5. README documents only the legacy script — the dashboard is invisible — warning

`README.md:27-43` never mentions `backend/`, `frontend/`,
`s3cure_communications.py`, `.env.example`, or how to run the dashboard; the
roadmap still lists ElevenLabs as future work though it's implemented. Add a
dashboard setup section, refresh file list/roadmap.

### 6. Clips played as raw bytes, header included, at an assumed format — warning

`voice_search_baiter.py:183-187` writes whole-file bytes to a PyAudio stream
opened as 44.1 kHz/mono/16-bit (lines 218-224): the RIFF header plays as a
click, and any clip in another format plays as noise/wrong speed. Use the
`wave` module to honor per-file params.

### 7. `s3cure_communications.py` runs its demo loop at import time — info

Lines 152-157 execute the 20-message example at module level. Wrap in
`if __name__ == "__main__":`.

### 8. 21 MB of WAVs committed directly, plus junk listing file — info

`scammer_soundboard/Walter Nelson/` is ~21 MB of uncompressed WAVs (nearly the
whole 22 MB tree); `filenames.txt` is a committed UTF-16 `dir` output artifact.
Consider Git LFS or compressed mp3/ogg; delete `filenames.txt`.

## TODOs

- [ ] Fix tier-1 filler list ("Sure Thing.wav" casing; missing "I understand.wav"); handle missing files gracefully
- [ ] Add `bluetooth_bridge.py` or remove `"bluetooth"` from the config Literal
- [ ] Update root requirements pins for Python 3.12 (pyaudio>=0.2.14, modern numpy)
- [ ] Include `file_path` in `clip_ready` WS payload; dedupe `addClip` by id
- [ ] Rewrite README to cover the backend/frontend dashboard and `.env.example`; refresh roadmap
- [ ] Play clips via the `wave` module (skip header, honor per-file format)
- [ ] Add main guard around the `s3cure_communications.py` demo loop
- [ ] Move WAVs to LFS/compressed formats; delete `filenames.txt`
