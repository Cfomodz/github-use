# Audit: Cfomodz/browser-osint

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read)

## Summary

Single-file Python CLI (`browser_osint.py`) that takes a browser screenshot and,
using OpenCV + Tesseract OCR, OCRs the bookmarks bar and locates/crops pinned
extension icons via template matching and contour detection, optionally running
each icon through a reverse-image-search API (SauceNAO/TinEye/Google). Output:
cropped PNGs + `results.json` in `output/`.

No committed secrets or injection vectors found — all keys come from env vars.

## Findings

### 1. Template images loaded relative to CWD, silently disabling browser detection — warning

`browser_osint.py:100-109` loads `firefox_menu.png`/`chrome_menu.png` as bare
relative paths gated on `os.path.exists()`. Run from anywhere but the repo root
and no templates load — `detect_menu_icon()` always falls back to the crude
"top-right 5%" heuristic and reports `browser_type: "unknown"`. Resolve against
`os.path.dirname(os.path.abspath(__file__))`.

### 2. Google reverse-image-search path is non-functional + leaks a file handle — warning

`reverse_image_search_google()` (lines 269-304): the Google Custom Search JSON
API is a GET text-search API and does not accept an uploaded image, so this POST
with a dummy `q='image'` can never work. The base64 `image_data` (lines 282-283)
is dead, and `open(image_path, 'rb')` at line 295 is never closed. Remove or
replace with a real reverse-image API.

### 3. Summary output prints "None" instead of fallback labels — warning

`main()` uses `ext.get('name', 'Unknown')` (lines 554-555), but `process()`
always sets those keys — to `None` on no-match — so the default never applies
and the CLI prints `1. None (confidence: None)`. Use `ext.get('name') or
'Unknown'`.

### 4. `detect_bookmarks_bar()` does no actual detection — info

Lines 40-52 run Canny + `HoughLinesP` and compute regions, then discard all of
it and return a fixed strip `(0, height*0.15, width, height*0.08)` (line 54).
Either use the Hough results or remove the dead computation and document the
heuristic.

### 5. README `results.json` schema is stale — info

`README.md:87-110` omits the top-level `browser_type` key and the real
`name`/`description`/`confidence`/`source_url` fields on `extensions[]`.
Regenerate the example from a real run.

### 6. Default SauceNAO path fails without an API key, contradicting README — info

`reverse_image_search_saucenao()` (lines 306-329) sends an empty `api_key` by
default; SauceNAO's JSON API requires one, returns non-JSON, `response.json()`
raises, gets swallowed, returns `None` — yet `README.md:64-65,115-117` says "no
API key required for basic use". Validate the key and fix the README.

### 7. Committed template assets `chrome_ext.png`/`firefox_ext.png` never used — info

`.gitignore:48-51` explicitly whitelists them but code only loads the `_menu`
templates — dead assets implying an unimplemented feature. Wire in or remove.

### 8. LICENSE has no copyright holder — info

`LICENSE:3` reads `Copyright (c) 2025` with no name. Add the owner.

## TODOs

- [ ] Resolve template paths relative to `__file__`
- [ ] Fix or remove the broken Google reverse-search; close leaked file handle; delete dead base64 code
- [ ] Use `ext.get('name') or 'Unknown'` in the summary output
- [ ] Make `detect_bookmarks_bar()` use its analysis or drop it and document the fixed heuristic
- [ ] Update README `results.json` example to the real schema
- [ ] Validate SauceNAO key; correct "no API key required" claim
- [ ] Remove or use `chrome_ext.png`/`firefox_ext.png`
- [ ] Add copyright holder to LICENSE
